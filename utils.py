"""
utils.py - Utilidades generales para el sistema de análisis de tráfico

Este módulo contiene funciones auxiliares y utilidades compartidas
por todos los componentes del sistema.
"""

import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Tuple, List, Dict, Any
import cv2
import numpy as np
from colorama import Fore, Style, init

# Inicializar colorama para colores en consola
init(autoreset=True)

# Configuración de logging
def setup_logger(name: str, log_file: str = None, level=logging.INFO) -> logging.Logger:
    """
    Configura un logger personalizado con formato específico
    
    Args:
        name: Nombre del logger
        log_file: Ruta del archivo de log (opcional)
        level: Nivel de logging
        
    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Formato del log
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler para consola
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Handler para archivo (opcional)
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def create_output_dirs(base_dir: str = "outputs") -> Dict[str, str]:
    """
    Crea directorios de salida para los resultados
    
    Args:
        base_dir: Directorio base para salidas
        
    Returns:
        Diccionario con rutas de directorios creados
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_session = os.path.join(base_dir, f"session_{timestamp}")
    
    dirs = {
        'base': output_session,
        'videos': os.path.join(output_session, 'videos'),
        'exports': os.path.join(output_session, 'exports'),
        'visualizations': os.path.join(output_session, 'visualizations'),
        'logs': os.path.join(output_session, 'logs')
    }
    
    for dir_path in dirs.values():
        os.makedirs(dir_path, exist_ok=True)
    
    return dirs


def get_video_properties(video_path: str) -> Dict[str, Any]:
    """
    Obtiene propiedades de un video
    
    Args:
        video_path: Ruta del video
        
    Returns:
        Diccionario con propiedades del video
    """
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        raise ValueError(f"No se pudo abrir el video: {video_path}")
    
    properties = {
        'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        'fps': cap.get(cv2.CAP_PROP_FPS),
        'frame_count': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
        'duration': int(cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS)),
        'codec': int(cap.get(cv2.CAP_PROP_FOURCC))
    }
    
    cap.release()
    return properties


def resize_frame(frame: np.ndarray, target_width: int = None, target_height: int = None) -> np.ndarray:
    """
    Redimensiona un frame manteniendo aspect ratio
    
    Args:
        frame: Frame a redimensionar
        target_width: Ancho objetivo (opcional)
        target_height: Alto objetivo (opcional)
        
    Returns:
        Frame redimensionado
    """
    height, width = frame.shape[:2]
    
    if target_width and not target_height:
        aspect_ratio = width / height
        target_height = int(target_width / aspect_ratio)
    elif target_height and not target_width:
        aspect_ratio = width / height
        target_width = int(target_height * aspect_ratio)
    elif not target_width and not target_height:
        return frame
    
    return cv2.resize(frame, (target_width, target_height), interpolation=cv2.INTER_AREA)


def draw_line(frame: np.ndarray, start: Tuple[int, int], end: Tuple[int, int], 
              color: Tuple[int, int, int] = (0, 255, 0), thickness: int = 2,
              label: str = None) -> np.ndarray:
    """
    Dibuja una línea en el frame con opción de etiqueta
    
    Args:
        frame: Frame donde dibujar
        start: Punto inicial (x, y)
        end: Punto final (x, y)
        color: Color BGR
        thickness: Grosor de la línea
        label: Etiqueta opcional
        
    Returns:
        Frame con línea dibujada
    """
    cv2.line(frame, start, end, color, thickness)
    
    if label:
        # Calcular punto medio para la etiqueta
        mid_x = (start[0] + end[0]) // 2
        mid_y = (start[1] + end[1]) // 2
        
        # Fondo para el texto
        text_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
        cv2.rectangle(frame, 
                     (mid_x - 5, mid_y - text_size[1] - 5),
                     (mid_x + text_size[0] + 5, mid_y + 5),
                     color, -1)
        
        # Texto
        cv2.putText(frame, label, (mid_x, mid_y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    return frame


def draw_bounding_box(frame: np.ndarray, bbox: Tuple[int, int, int, int],
                      label: str = None, color: Tuple[int, int, int] = (0, 255, 0),
                      thickness: int = 2) -> np.ndarray:
    """
    Dibuja un bounding box con etiqueta
    
    Args:
        frame: Frame donde dibujar
        bbox: Bounding box (x1, y1, x2, y2)
        label: Etiqueta opcional
        color: Color BGR
        thickness: Grosor del borde
        
    Returns:
        Frame con bounding box dibujado
    """
    x1, y1, x2, y2 = map(int, bbox)
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
    
    if label:
        # Fondo para el texto
        text_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
        cv2.rectangle(frame,
                     (x1, y1 - text_size[1] - 10),
                     (x1 + text_size[0] + 10, y1),
                     color, -1)
        
        # Texto
        cv2.putText(frame, label, (x1 + 5, y1 - 5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
    
    return frame


def calculate_centroid(bbox: Tuple[int, int, int, int]) -> Tuple[int, int]:
    """
    Calcula el centroide de un bounding box
    
    Args:
        bbox: Bounding box (x1, y1, x2, y2)
        
    Returns:
        Coordenadas del centroide (x, y)
    """
    x1, y1, x2, y2 = bbox
    cx = int((x1 + x2) / 2)
    cy = int((y1 + y2) / 2)
    return (cx, cy)


def point_line_distance(point: Tuple[float, float], line_start: Tuple[float, float], 
                        line_end: Tuple[float, float]) -> float:
    """
    Calcula la distancia de un punto a una línea
    
    Args:
        point: Punto (x, y)
        line_start: Inicio de línea (x, y)
        line_end: Fin de línea (x, y)
        
    Returns:
        Distancia perpendicular del punto a la línea
    """
    x0, y0 = point
    x1, y1 = line_start
    x2, y2 = line_end
    
    numerator = abs((y2 - y1) * x0 - (x2 - x1) * y0 + x2 * y1 - y2 * x1)
    denominator = np.sqrt((y2 - y1)**2 + (x2 - x1)**2)
    
    if denominator == 0:
        return float('inf')
    
    return numerator / denominator


def check_line_crossing(prev_point: Tuple[int, int], curr_point: Tuple[int, int],
                       line_start: Tuple[int, int], line_end: Tuple[int, int]) -> bool:
    """
    Verifica si un objeto cruzó una línea entre dos puntos
    
    Args:
        prev_point: Posición anterior del objeto
        curr_point: Posición actual del objeto
        line_start: Inicio de la línea de conteo
        line_end: Fin de la línea de conteo
        
    Returns:
        True si cruzó la línea, False en caso contrario
    """
    def ccw(A, B, C):
        return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])
    
    return ccw(prev_point, line_start, line_end) != ccw(curr_point, line_start, line_end) and \
           ccw(prev_point, curr_point, line_start) != ccw(prev_point, curr_point, line_end)


def get_crossing_direction(prev_point: Tuple[int, int], curr_point: Tuple[int, int],
                          line_start: Tuple[int, int], line_end: Tuple[int, int]) -> str:
    """
    Determina la dirección del cruce (arriba->abajo, izquierda->derecha, etc.)
    
    Args:
        prev_point: Posición anterior
        curr_point: Posición actual
        line_start: Inicio de línea
        line_end: Fin de línea
        
    Returns:
        Dirección como string ('up_to_down', 'down_to_up', 'left_to_right', 'right_to_left')
    """
    # Calcular vector de la línea
    line_vec = (line_end[0] - line_start[0], line_end[1] - line_start[1])
    
    # Calcular vector de movimiento
    movement_vec = (curr_point[0] - prev_point[0], curr_point[1] - prev_point[1])
    
    # Producto cruz para determinar lado
    cross_product = line_vec[0] * movement_vec[1] - line_vec[1] * movement_vec[0]
    
    # Determinar si la línea es más horizontal o vertical
    if abs(line_vec[0]) > abs(line_vec[1]):
        # Línea horizontal
        return 'up_to_down' if cross_product > 0 else 'down_to_up'
    else:
        # Línea vertical
        return 'left_to_right' if cross_product > 0 else 'right_to_left'


def format_time(seconds: float) -> str:
    """
    Formatea segundos en formato HH:MM:SS
    
    Args:
        seconds: Tiempo en segundos
        
    Returns:
        String formateado
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def print_colored(message: str, color: str = 'white', style: str = 'normal'):
    """
    Imprime mensaje con color en consola
    
    Args:
        message: Mensaje a imprimir
        color: Color del texto
        style: Estilo del texto
    """
    colors = {
        'red': Fore.RED,
        'green': Fore.GREEN,
        'yellow': Fore.YELLOW,
        'blue': Fore.BLUE,
        'magenta': Fore.MAGENTA,
        'cyan': Fore.CYAN,
        'white': Fore.WHITE
    }
    
    styles = {
        'normal': Style.NORMAL,
        'bright': Style.BRIGHT,
        'dim': Style.DIM
    }
    
    color_code = colors.get(color.lower(), Fore.WHITE)
    style_code = styles.get(style.lower(), Style.NORMAL)
    
    print(f"{style_code}{color_code}{message}{Style.RESET_ALL}")


# Clases de objetos detectables con sus colores asociados
# Colores en BGR — uno distinto por clase para identificación visual rápida
OBJECT_CLASSES = {
    # Tus 11 clases entrenadas
    'auto':      {'name': 'Auto',      'color': (  0, 200, 255), 'category': 'vehicle'},
    'bus':       {'name': 'Bus',       'color': (226,  43, 138), 'category': 'vehicle'},
    'camion':    {'name': 'Camión',    'color': (  0,   0, 255), 'category': 'vehicle'},
    'camioneta': {'name': 'Camioneta', 'color': (128,   0, 128), 'category': 'vehicle'},
    'combi':     {'name': 'Combi',     'color': (  0, 165, 255), 'category': 'vehicle'},
    'furgon':    {'name': 'Furgón',    'color': ( 50, 205,  50), 'category': 'vehicle'},
    'microbus':  {'name': 'Microbús',  'color': (255, 128,   0), 'category': 'vehicle'},
    'moto':      {'name': 'Moto',      'color': (  0, 255, 255), 'category': 'vehicle'},
    'omnibus':   {'name': 'Omnibus',   'color': (147,  20, 255), 'category': 'vehicle'},
    'peaton':    {'name': 'Peatón',    'color': (255, 255,   0), 'category': 'pedestrian'},
    'trailer':   {'name': 'Tráiler',   'color': ( 42,  42, 165), 'category': 'vehicle'},
}


def get_object_color(class_name: str) -> Tuple[int, int, int]:
    """
    Obtiene el color asociado a una clase de objeto
    
    Args:
        class_name: Nombre de la clase
        
    Returns:
        Color BGR
    """
    return OBJECT_CLASSES.get(class_name, {}).get('color', (255, 255, 255))


def get_object_spanish_name(class_name: str) -> str:
    """
    Obtiene el nombre en español de una clase
    
    Args:
        class_name: Nombre de la clase en inglés
        
    Returns:
        Nombre en español
    """
    return OBJECT_CLASSES.get(class_name, {}).get('name', class_name)


def validate_video_file(video_path: str) -> bool:
    """
    Valida que un archivo de video sea válido y legible
    
    Args:
        video_path: Ruta del video
        
    Returns:
        True si es válido, False en caso contrario
    """
    if not os.path.exists(video_path):
        return False
    
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return False
        
        ret, frame = cap.read()
        cap.release()
        return ret and frame is not None
    except:
        return False


def estimate_processing_time(video_path: str, fps_processing: float = 15.0) -> float:
    """
    Estima el tiempo de procesamiento de un video
    
    Args:
        video_path: Ruta del video
        fps_processing: FPS estimado de procesamiento
        
    Returns:
        Tiempo estimado en segundos
    """
    try:
        props = get_video_properties(video_path)
        total_frames = props['frame_count']
        return total_frames / fps_processing
    except:
        return 0.0


if __name__ == "__main__":
    # Pruebas de utilidades
    print_colored("=== Pruebas de Utilidades ===", "cyan", "bright")
    print_colored("✓ Módulo de utilidades cargado correctamente", "green")