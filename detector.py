"""
detector.py - Módulo de detección de objetos con YOLOv8

Este módulo implementa la detección de vehículos y peatones usando
el modelo YOLOv8 pre-entrenado en COCO dataset.
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import torch
import ultralytics
from ultralytics import YOLO

from utils import setup_logger, get_object_color, get_object_spanish_name, OBJECT_CLASSES

# Configurar logger
logger = setup_logger('detector')

# Agregar globals seguros para PyTorch 2.6+
try:
    import ultralytics.nn.tasks
    import ultralytics.nn.modules
    import torch.nn.modules.container
    import torch.nn.modules.conv
    import torch.nn.modules.batchnorm
    import torch.nn.modules.activation
    import torch.nn.modules.pooling
    import torch.nn.modules.linear

    torch.serialization.add_safe_globals([
        ultralytics.nn.tasks.DetectionModel,
        ultralytics.nn.modules.Conv,
        torch.nn.modules.container.Sequential,
        torch.nn.modules.conv.Conv2d,
        torch.nn.modules.batchnorm.BatchNorm2d,
        torch.nn.modules.activation.SiLU,
        torch.nn.modules.pooling.AdaptiveAvgPool2d,
        torch.nn.modules.linear.Linear,
    ])
    logger.info("Globals seguros agregados para PyTorch 2.6+")
except Exception as e:
    logger.warning(f"No se pudieron agregar globals seguros: {e}")

from collections import deque, Counter

class LabelStabilizer:
    """Estabiliza etiquetas de clases usando votación por ventana de frames."""
    
    def __init__(self, window=7, min_confidence=0.60):
        self.history = {}       # track_id -> deque de class_names
        self.last_stable = {}   # track_id -> última etiqueta confiable
        self.window = window
        self.min_confidence = min_confidence
    
    def stabilize(self, track_id: int, class_name: str, confidence: float) -> str:
        # Si confianza baja y ya tenemos historial, mantener la última estable
        if confidence < self.min_confidence and track_id in self.last_stable:
            return self.last_stable[track_id]
        
        if track_id not in self.history:
            self.history[track_id] = deque(maxlen=self.window)
        
        self.history[track_id].append(class_name)
        stable = Counter(self.history[track_id]).most_common(1)[0][0]
        self.last_stable[track_id] = stable
        return stable
    
    def reset(self):
        self.history.clear()
        self.last_stable.clear()
class ObjectDetector:
    """
    Detector de objetos basado en YOLOv8
    
    Attributes:
        model: Modelo YOLO cargado
        confidence_threshold: Umbral mínimo de confianza
        target_classes: Lista de clases a detectar
        device: Dispositivo de cómputo (cpu/cuda)
    """
    
    def __init__(self, 
                 model_name: str = 'yolov8n.pt',
                 confidence_threshold: float = 0.5,
                 target_classes: Optional[List[str]] = None,
                 device: str = 'auto'):
        """
        Inicializa el detector
        
        Args:
            model_name: Nombre del modelo YOLO a cargar
            confidence_threshold: Umbral de confianza (0.0-1.0)
            target_classes: Clases específicas a detectar (None = todas las disponibles)
            device: 'cpu', 'cuda', o 'auto' para detección automática
        """
        self.confidence_threshold = confidence_threshold
        self.model_name = model_name
        
        # Determinar dispositivo
        if device == 'auto':
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        else:
            self.device = device
        
        logger.info(f"Inicializando detector en dispositivo: {self.device}")
        
        # Cargar modelo
        try:
            # Para compatibilidad con PyTorch 2.6+, usar weights_only=False para modelos YOLO oficiales
            # ya que provienen de fuentes confiables (Ultralytics)
            import os
            if hasattr(torch, 'load') and hasattr(torch.load, '__code__'):
                # Monkey patch temporal para permitir carga de modelos YOLO
                original_load = torch.load
                def patched_load(*args, **kwargs):
                    if 'weights_only' not in kwargs:
                        kwargs['weights_only'] = False
                    return original_load(*args, **kwargs)
                torch.load = patched_load
            
            self.model = YOLO(model_name)
            self.model.to(self.device)
            logger.info(f"Modelo {model_name} cargado exitosamente")
        except Exception as e:
            logger.error(f"Error al cargar modelo: {e}")
            raise
        
        # Configurar clases objetivo
        if target_classes is None:
            # Por defecto, detectar vehículos y peatones
            self.target_classes = list(OBJECT_CLASSES.keys())
        else:
            self.target_classes = target_classes
        
        # Mapeo de clases COCO a nombres
        self.class_names = self.model.names
        
        # Obtener IDs de clases objetivo
        self.target_class_ids = self._get_target_class_ids()
        
        logger.info(f"Clases objetivo: {self.target_classes}")
        logger.info(f"IDs de clases: {self.target_class_ids}")

        # Al final del __init__, después de los logger.info:
        self.stabilizer = LabelStabilizer(window=7, min_confidence=0.60)
    
    def _get_target_class_ids(self) -> List[int]:
        """
        Obtiene los IDs de las clases objetivo desde el modelo
        
        Returns:
            Lista de IDs de clases
        """
        target_ids = []
        for class_name in self.target_classes:
            for class_id, coco_name in self.class_names.items():
                if coco_name == class_name:
                    target_ids.append(class_id)
                    break
        return target_ids
    
    def detect(self, frame: np.ndarray, conf_threshold: Optional[float] = None) -> List[Dict]:
        """
        Realiza detección en un frame
        
        Args:
            frame: Frame de video (BGR)
            conf_threshold: Umbral de confianza (override temporal)
            
        Returns:
            Lista de detecciones con formato:
            [
                {
                    'bbox': (x1, y1, x2, y2),
                    'confidence': float,
                    'class_id': int,
                    'class_name': str,
                    'class_spanish': str,
                    'centroid': (cx, cy)
                },
                ...
            ]
        """
        threshold = conf_threshold if conf_threshold is not None else self.confidence_threshold
        
        # Realizar predicción
        try:
            results = self.model.track(
    frame,
    tracker="bytetrack.yaml",
    persist=True,           # mantiene IDs entre frames
    conf=threshold,
    iou=0.45,
    agnostic_nms=True,
    verbose=False
)
        except Exception as e:
            logger.error(f"Error en detección: {e}")
            return []
        
        # Procesar resultados
        detections = []
        
        if len(results) > 0 and results[0].boxes is not None:
            boxes = results[0].boxes
            
            for i in range(len(boxes)):
                # Extraer datos
                bbox = boxes.xyxy[i].cpu().numpy()  # x1, y1, x2, y2
                conf = float(boxes.conf[i].cpu().numpy())
                class_id = int(boxes.cls[i].cpu().numpy())
                class_name = self.class_names[class_id]
                
                # Calcular centroide
                x1, y1, x2, y2 = bbox
                cx = int((x1 + x2) / 2)
                cy = int((y1 + y2) / 2)
                
                # Estabilizar etiqueta con track_id
                track_id = int(boxes.id[i].cpu().numpy()) if boxes.id is not None else -1
                stable_class = self.stabilizer.stabilize(track_id, class_name, conf)

                # Crear detección
                detection = {
                    'bbox': tuple(map(int, bbox)),
                    'confidence': conf,
                    'class_id': class_id,
                    'class_name': stable_class,
                    'class_spanish': get_object_spanish_name(stable_class),
                    'track_id': track_id,
                    'centroid': (cx, cy),
                    'area': (x2 - x1) * (y2 - y1)
                }
                
                detections.append(detection)
        
        return detections
    
    def detect_batch(self, frames: List[np.ndarray], 
                     conf_threshold: Optional[float] = None) -> List[List[Dict]]:
        """
        Realiza detección en batch de frames (más eficiente)
        
        Args:
            frames: Lista de frames
            conf_threshold: Umbral de confianza
            
        Returns:
            Lista de listas de detecciones
        """
        threshold = conf_threshold if conf_threshold is not None else self.confidence_threshold
        
        try:
            results = self.model.predict(
                frames,
                conf=threshold,
                classes=self.target_class_ids if self.target_class_ids else None,
                verbose=False,
                device=self.device,
                stream=True
            )
        except Exception as e:
            logger.error(f"Error en detección batch: {e}")
            return [[] for _ in frames]
        
        all_detections = []
        
        for result in results:
            detections = []
            
            if result.boxes is not None:
                boxes = result.boxes
                
                for i in range(len(boxes)):
                    bbox = boxes.xyxy[i].cpu().numpy()
                    conf = float(boxes.conf[i].cpu().numpy())
                    class_id = int(boxes.cls[i].cpu().numpy())
                    class_name = self.class_names[class_id]
                    
                    x1, y1, x2, y2 = bbox
                    cx = int((x1 + x2) / 2)
                    cy = int((y1 + y2) / 2)

                    track_id = int(boxes.id[i].cpu().numpy()) if boxes.id is not None else -1
                    stable_class = self.stabilizer.stabilize(track_id, class_name, conf)
                    
                    detection = {
                        'bbox': tuple(map(int, bbox)),
                        'confidence': conf,
                        'class_id': class_id,
                        'class_name': stable_class,                          # ← estabilizado
                        'class_spanish': get_object_spanish_name(stable_class),  # ← estabilizado
                        'track_id': track_id,
                        'centroid': (cx, cy),
                        'area': (x2 - x1) * (y2 - y1)
                    }
                    
                    detections.append(detection)
            
            all_detections.append(detections)
        
        return all_detections
    
    def draw_detections(self, frame: np.ndarray, detections: List[Dict],
                       show_confidence: bool = True,
                       show_class: bool = True) -> np.ndarray:
        """
        Dibuja las detecciones en el frame
        
        Args:
            frame: Frame donde dibujar
            detections: Lista de detecciones
            show_confidence: Mostrar confianza
            show_class: Mostrar clase
            
        Returns:
            Frame con detecciones dibujadas
        """
        frame_copy = frame.copy()
        
        for det in detections:
            bbox = det['bbox']
            class_name = det['class_name']
            class_spanish = det['class_spanish']
            confidence = det['confidence']
            centroid = det['centroid']
            
            # Color según clase
            color = get_object_color(class_name)
            
            # Dibujar bounding box
            x1, y1, x2, y2 = bbox
            cv2.rectangle(frame_copy, (x1, y1), (x2, y2), color, 2)
            
            # Preparar label
            label_parts = []
            if show_class:
                label_parts.append(class_spanish)
            if show_confidence:
                label_parts.append(f"{confidence:.2f}")
            
            label = " - ".join(label_parts) if label_parts else ""
            
            if label:
                # Fondo para texto
                text_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
                cv2.rectangle(frame_copy,
                            (x1, y1 - text_size[1] - 10),
                            (x1 + text_size[0] + 10, y1),
                            color, -1)
                
                # Texto
                cv2.putText(frame_copy, label, (x1 + 5, y1 - 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            
            # Dibujar centroide
            cv2.circle(frame_copy, centroid, 3, color, -1)
        
        return frame_copy
    
    def get_statistics(self, detections: List[Dict]) -> Dict[str, int]:
        """
        Obtiene estadísticas de las detecciones
        
        Args:
            detections: Lista de detecciones
            
        Returns:
            Diccionario con conteos por clase
        """
        stats = {}
        
        for det in detections:
            class_spanish = det['class_spanish']
            stats[class_spanish] = stats.get(class_spanish, 0) + 1
        
        return stats
    
    def filter_detections_by_area(self, detections: List[Dict],
                                  min_area: float = 0,
                                  max_area: float = float('inf')) -> List[Dict]:
        """
        Filtra detecciones por área del bounding box
        
        Args:
            detections: Lista de detecciones
            min_area: Área mínima
            max_area: Área máxima
            
        Returns:
            Detecciones filtradas
        """
        return [det for det in detections if min_area <= det['area'] <= max_area]
    
    def update_confidence_threshold(self, new_threshold: float):
        """
        Actualiza el umbral de confianza
        
        Args:
            new_threshold: Nuevo umbral (0.0-1.0)
        """
        if 0.0 <= new_threshold <= 1.0:
            self.confidence_threshold = new_threshold
            logger.info(f"Umbral de confianza actualizado a: {new_threshold}")
        else:
            logger.warning(f"Umbral inválido: {new_threshold}. Debe estar entre 0 y 1")
    
    def update_target_classes(self, new_classes: List[str]):
        """
        Actualiza las clases objetivo
        
        Args:
            new_classes: Nueva lista de clases
        """
        self.target_classes = new_classes
        self.target_class_ids = self._get_target_class_ids()
        logger.info(f"Clases objetivo actualizadas: {new_classes}")
    
    def get_model_info(self) -> Dict[str, any]:
        """
        Obtiene información del modelo
        
        Returns:
            Diccionario con información del modelo
        """
        return {
            'model_name': self.model_name,
            'device': self.device,
            'confidence_threshold': self.confidence_threshold,
            'target_classes': self.target_classes,
            'total_classes': len(self.class_names)
        }


# Función auxiliar para inicializar detector con configuración por defecto
def create_detector(confidence: float = 0.5, 
                   model_size: str = 'n',
                   classes: Optional[List[str]] = None,
                   use_peruvian_model: bool = True) -> ObjectDetector:
    """
    Función helper para crear un detector con configuración simplificada
    """
    # Ruta del modelo peruano
    peruvian_model = Path("models/vehiculos_peruanos.pt")
    
    if use_peruvian_model and peruvian_model.exists():
        model_name = str(peruvian_model)
        logger.info("Usando modelo peruano: vehiculos_peruanos.pt")
    else:
        model_name = f"yolov8{model_size}.pt"
        if use_peruvian_model:
            logger.warning("Modelo peruano no encontrado, usando YOLOv8 base")
    
    return ObjectDetector(
        model_name=model_name,
        confidence_threshold=confidence,
        target_classes=classes,
        device='auto'
    )


if __name__ == "__main__":
    # Pruebas del detector
    print("=== Pruebas del Detector ===")
    
    # Crear detector
    detector = create_detector(confidence=0.5, model_size='n')
    
    # Mostrar info
    info = detector.get_model_info()
    print(f"Modelo cargado: {info['model_name']}")
    print(f"Dispositivo: {info['device']}")
    print(f"Clases objetivo: {info['target_classes']}")
    
    print("\n✓ Módulo detector funcionando correctamente")
