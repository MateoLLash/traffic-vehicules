"""
counter.py - Módulo de conteo con líneas configurables

Este módulo implementa un sistema de conteo inteligente que permite
definir múltiples líneas de conteo y detectar cruces con dirección.
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from collections import defaultdict
import cv2

from utils import (setup_logger, check_line_crossing, get_crossing_direction,
                   draw_line, get_object_color)
from tracker import Track

# Configurar logger
logger = setup_logger('counter')


class CountingLine:
    """
    Representa una línea de conteo
    
    Attributes:
        line_id: ID único de la línea
        name: Nombre descriptivo
        start: Punto inicial (x, y)
        end: Punto final (x, y)
        color: Color BGR de la línea
        thickness: Grosor de la línea
        counts: Diccionario de conteos por clase y dirección
        crossings: Historial de cruces
    """
    
    def __init__(self,
                 line_id: int,
                 start: Tuple[int, int],
                 end: Tuple[int, int],
                 name: str = None,
                 color: Tuple[int, int, int] = (0, 255, 0),
                 thickness: int = 3):
        """
        Inicializa una línea de conteo
        
        Args:
            line_id: ID único
            start: Punto inicial (x, y)
            end: Punto final (x, y)
            name: Nombre opcional
            color: Color BGR
            thickness: Grosor en píxeles
        """
        self.line_id = line_id
        self.start = start
        self.end = end
        self.name = name or f"Línea {line_id}"
        self.color = color
        self.thickness = thickness
        
        # Conteos por clase y dirección
        self.counts = defaultdict(lambda: {'total': 0, 'up_to_down': 0, 'down_to_up': 0,
                                          'left_to_right': 0, 'right_to_left': 0})
        
        # Historial de cruces
        self.crossings = []
        
        # IDs de tracks que ya cruzaron (para evitar duplicados)
        self.crossed_tracks = set()
    
    def check_crossing(self, track, prev_centroid, curr_centroid, timestamp):
    
    # Obtener bbox actual
        bbox = track.get_current_bbox()
        x1, y1, x2, y2 = bbox
    
    # Desplazamiento entre frames
        dx = curr_centroid[0] - prev_centroid[0]
        dy = curr_centroid[1] - prev_centroid[1]
    
    # 5 puntos del frame actual (centroide + 4 bordes del bbox)
        puntos_curr = [
            curr_centroid,
            (x1, (y1+y2)//2),        # borde izquierdo
            (x2, (y1+y2)//2),        # borde derecho
            ((x1+x2)//2, y1),        # borde superior
            ((x1+x2)//2, y2),        # borde inferior ← el que faltaba para buses/combis
        ]
    
    # 5 puntos del frame anterior (desplazados hacia atrás)
        puntos_prev = [
            prev_centroid,
            (x1 - dx, (y1+y2)//2 - dy),
            (x2 - dx, (y1+y2)//2 - dy),
            ((x1+x2)//2 - dx, y1 - dy),
            ((x1+x2)//2 - dx, y2 - dy),
        ]
    
    # Cruce si CUALQUIER punto del bbox cruza la línea
        crossed = any(
            check_line_crossing(pp, cp, self.start, self.end)
            for pp, cp in zip(puntos_prev, puntos_curr)
        )
    
        if not crossed:
            return None
    
    # Evitar duplicados
        if track.track_id in self.crossed_tracks:
            return None
    
    # Dirección usando centroide (más estable para dirección)
        direction = get_crossing_direction(
            prev_centroid, curr_centroid, self.start, self.end
        )
    
        crossing_info = {
            'track_id':     track.track_id,
            'class_name':   track.class_name,
            'class_spanish': track.class_spanish,
            'direction':    direction,
            'timestamp':    timestamp,
            'line_id':      self.line_id,
            'line_name':    self.name,
            'centroid':     curr_centroid
        }
    
        self.counts[track.class_spanish]['total'] += 1
        self.counts[track.class_spanish][direction] += 1
        self.crossings.append(crossing_info)
        self.crossed_tracks.add(track.track_id)
        
        logger.info(f"Cruce detectado: {track.class_spanish} ({track.track_id}) - "
                f"Línea: {self.name} - Dirección: {direction}")
        
        return crossing_info
    
    def get_total_count(self) -> int:
        """Obtiene el conteo total de todos los objetos"""
        return sum(counts['total'] for counts in self.counts.values())
    
    def get_count_by_class(self, class_spanish: str) -> int:
        """Obtiene el conteo de una clase específica"""
        return self.counts[class_spanish]['total']
    
    def get_count_by_direction(self, direction: str) -> int:
        """Obtiene el conteo total en una dirección"""
        return sum(counts[direction] for counts in self.counts.values())
    
    def get_summary(self) -> Dict:
        """
        Obtiene resumen de conteos
        
        Returns:
            Diccionario con resumen completo
        """
        return {
            'line_id': self.line_id,
            'line_name': self.name,
            'total_count': self.get_total_count(),
            'counts_by_class': dict(self.counts),
            'crossings': self.crossings
        }
    
    def draw(self, frame: np.ndarray, show_counts: bool = True) -> np.ndarray:
        """
        Dibuja la línea en el frame
        
        Args:
            frame: Frame donde dibujar
            show_counts: Mostrar conteos
            
        Returns:
            Frame con línea dibujada
        """
        # Dibujar línea
        cv2.line(frame, self.start, self.end, self.color, self.thickness)
        
        if show_counts:
            # Calcular posición del texto
            mid_x = (self.start[0] + self.end[0]) // 2
            mid_y = (self.start[1] + self.end[1]) // 2
            
            # Texto con conteo total
            total = self.get_total_count()
            text = f"{self.name}: {total}"
            
            # Fondo para el texto
            text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
            cv2.rectangle(frame,
                         (mid_x - text_size[0]//2 - 10, mid_y - text_size[1] - 10),
                         (mid_x + text_size[0]//2 + 10, mid_y + 10),
                         self.color, -1)
            
            # Texto
            cv2.putText(frame, text,
                       (mid_x - text_size[0]//2, mid_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        return frame
    
    def reset(self):
        """Resetea los conteos"""
        self.counts = defaultdict(lambda: {'total': 0, 'up_to_down': 0, 'down_to_up': 0,
                                          'left_to_right': 0, 'right_to_left': 0})
        self.crossings = []
        self.crossed_tracks = set()


class TrafficCounter:
    """
    Sistema de conteo de tráfico con múltiples líneas
    
    Attributes:
        lines: Lista de líneas de conteo
        fps: FPS del video
        total_frames: Total de frames procesados
        start_time: Timestamp de inicio
    """
    
    def __init__(self, fps: float = 30.0):
        """
        Inicializa el contador
        
        Args:
            fps: FPS del video
        """
        self.lines = []
        self.fps = fps
        self.total_frames = 0
        self.start_time = None
        
        # Historial de tracks procesados
        self.track_history = {}
        
        logger.info(f"TrafficCounter inicializado con FPS: {fps}")
    
    def add_line(self,
                 start: Tuple[int, int],
                 end: Tuple[int, int],
                 name: str = None,
                 color: Tuple[int, int, int] = None) -> CountingLine:
        """
        Agrega una nueva línea de conteo
        
        Args:
            start: Punto inicial
            end: Punto final
            name: Nombre opcional
            color: Color opcional
            
        Returns:
            Línea creada
        """
        line_id = len(self.lines) + 1
        
        # Color automático si no se proporciona
        if color is None:
            colors = [(0, 255, 0), (255, 0, 0), (0, 0, 255), 
                     (255, 255, 0), (255, 0, 255), (0, 255, 255)]
            color = colors[(line_id - 1) % len(colors)]
        
        line = CountingLine(line_id, start, end, name, color)
        self.lines.append(line)
        
        logger.info(f"Línea agregada: {line.name} - {start} a {end}")
        return line
    
    def remove_line(self, line_id: int):
        """
        Elimina una línea por ID
        
        Args:
            line_id: ID de la línea a eliminar
        """
        self.lines = [line for line in self.lines if line.line_id != line_id]
        logger.info(f"Línea {line_id} eliminada")
    
    def get_line(self, line_id: int) -> Optional[CountingLine]:
        """
        Obtiene una línea por ID
        
        Args:
            line_id: ID de la línea
            
        Returns:
            Línea o None
        """
        for line in self.lines:
            if line.line_id == line_id:
                return line
        return None
    
    def update(self, tracks: List[Track], frame_number: int) -> List[Dict]:
        """
        Actualiza el contador con los tracks del frame actual
        
        Args:
            tracks: Lista de tracks activos
            frame_number: Número del frame
            
        Returns:
            Lista de cruces detectados en este frame
        """
        self.total_frames = frame_number
        timestamp = frame_number / self.fps
        
        if self.start_time is None:
            self.start_time = timestamp
        
        all_crossings = []
        
        # Procesar cada track
        for track in tracks:
            # Necesitamos al menos 2 posiciones para detectar cruce
            if len(track.centroids) < 2:
                continue
            
            # Obtener posiciones actual y anterior
            curr_centroid = track.centroids[-1]
            prev_centroid = track.centroids[-2]
            
            # Verificar cruce en cada línea
            for line in self.lines:
                crossing = line.check_crossing(track, prev_centroid, curr_centroid, timestamp)
                if crossing:
                    all_crossings.append(crossing)
        
        return all_crossings
    
    def draw_lines(self, frame: np.ndarray, show_counts: bool = True) -> np.ndarray:
        """
        Dibuja todas las líneas en el frame
        
        Args:
            frame: Frame donde dibujar
            show_counts: Mostrar conteos
            
        Returns:
            Frame con líneas dibujadas
        """
        for line in self.lines:
            frame = line.draw(frame, show_counts)
        return frame
    
    def get_total_counts(self) -> Dict[str, int]:
        """
        Obtiene conteos totales de todas las líneas
        
        Returns:
            Diccionario con conteos por clase
        """
        total_counts = defaultdict(int)
        
        for line in self.lines:
            for class_spanish, counts in line.counts.items():
                total_counts[class_spanish] += counts['total']
        
        return dict(total_counts)
    
    def get_counts_by_line(self) -> List[Dict]:
        """
        Obtiene conteos separados por línea
        
        Returns:
            Lista de diccionarios con conteos por línea
        """
        return [line.get_summary() for line in self.lines]
    
    def get_all_crossings(self) -> List[Dict]:
        """
        Obtiene todos los cruces registrados
        
        Returns:
            Lista de todos los cruces
        """
        all_crossings = []
        for line in self.lines:
            all_crossings.extend(line.crossings)
        
        # Ordenar por timestamp
        all_crossings.sort(key=lambda x: x['timestamp'])
        return all_crossings
    
    def get_statistics(self) -> Dict:
        """
        Obtiene estadísticas completas del conteo
        
        Returns:
            Diccionario con estadísticas
        """
        total_counts = self.get_total_counts()
        counts_by_line = self.get_counts_by_line()
        all_crossings = self.get_all_crossings()
        
        # Calcular promedios
        elapsed_time = self.total_frames / self.fps  # segundos
        elapsed_minutes = elapsed_time / 60
        
        avg_per_minute = {}
        if elapsed_minutes > 0:
            for class_name, count in total_counts.items():
                avg_per_minute[class_name] = count / elapsed_minutes
        
        return {
            'total_counts': total_counts,
            'counts_by_line': counts_by_line,
            'total_crossings': len(all_crossings),
            'total_lines': len(self.lines),
            'elapsed_time': elapsed_time,
            'elapsed_minutes': elapsed_minutes,
            'average_per_minute': avg_per_minute
        }
    
    def get_time_series_data(self, interval_seconds: int = 60) -> Dict:
        """
        Obtiene datos de series temporales para análisis
        
        Args:
            interval_seconds: Intervalo de agrupación en segundos
            
        Returns:
            Diccionario con series temporales
        """
        all_crossings = self.get_all_crossings()
        
        if not all_crossings:
            return {'intervals': [], 'counts': {}}
        
        # Determinar rangos de tiempo
        max_time = max(c['timestamp'] for c in all_crossings)
        num_intervals = int(max_time / interval_seconds) + 1
        
        # Inicializar conteos por intervalo
        time_series = defaultdict(lambda: defaultdict(int))
        
        # Agrupar cruces por intervalo
        for crossing in all_crossings:
            interval_idx = int(crossing['timestamp'] / interval_seconds)
            class_name = crossing['class_spanish']
            time_series[interval_idx][class_name] += 1
        
        # Formatear resultado
        intervals = list(range(num_intervals))
        counts_by_class = defaultdict(list)
        
        # Obtener todas las clases
        all_classes = set()
        for crossing in all_crossings:
            all_classes.add(crossing['class_spanish'])
        
        # Llenar datos para cada clase
        for class_name in all_classes:
            for interval in intervals:
                count = time_series[interval].get(class_name, 0)
                counts_by_class[class_name].append(count)
        
        return {
            'intervals': intervals,
            'interval_seconds': interval_seconds,
            'counts': dict(counts_by_class),
            'timestamps': [i * interval_seconds for i in intervals]
        }
    
    def reset(self):
        """Resetea todos los conteos"""
        for line in self.lines:
            line.reset()
        self.total_frames = 0
        self.start_time = None
        self.track_history = {}
        logger.info("Contador reseteado")
    
    def clear_lines(self):
        """Elimina todas las líneas"""
        self.lines = []
        logger.info("Todas las líneas eliminadas")


if __name__ == "__main__":
    # Pruebas del contador
    print("=== Pruebas del Counter ===")
    
    # Crear contador
    counter = TrafficCounter(fps=30.0)
    
    # Agregar líneas
    line1 = counter.add_line((100, 300), (500, 300), "Línea Norte")
    line2 = counter.add_line((300, 100), (300, 500), "Línea Este")
    
    print(f"Líneas agregadas: {len(counter.lines)}")
    
    # Estadísticas
    stats = counter.get_statistics()
    print(f"Estadísticas: Total de líneas = {stats['total_lines']}")
    
    print("\n✓ Módulo counter funcionando correctamente")
