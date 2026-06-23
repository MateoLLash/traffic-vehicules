import os

# --- RUTAS DEL PROYECTO ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
TEMP_DIR = os.path.join(BASE_DIR, "temp")

# Crear carpetas si no existen
for folder in [OUTPUT_DIR, TEMPLATES_DIR, TEMP_DIR]:
    os.makedirs(folder, exist_ok=True)

# --- CONFIGURACIÓN DE DETECCIÓN ---
MODEL_PATH = "yolov8n.pt"  # Puedes cambiar a 'yolov8s.pt' o 'yolov8m.pt' para más precisión.
DEFAULT_MODEL_SIZE = 's'  # 'n' = nano, 's' = small, 'm' = medium, 'l' = large
CONFIDENCE_THRESHOLD = 0.5  # Umbral de confianza más alto reduce detecciones espurias
IOU_THRESHOLD = 0.5  # Umbral de IoU más alto mejora la asociación de objetos
DEVICE = "0"  # 'cpu' o '0' (para GPU NVIDIA)

# --- CONFIGURACIÓN DE TRACKING ---
TRACKER_MAX_AGE = 15  # Frames antes de eliminar un track sin actualizaciones
TRACKER_MIN_HITS = 2  # Hits mínimos para considerar un track válido
TRACKER_IOU_THRESHOLD = 0.4  # Umbral de IoU para asociar detecciones a tracks
TRACKER_DISTANCE_THRESHOLD = 60  # Distancia máxima en píxeles para asociar tracks

# --- CLASIFICACIÓN DE VEHÍCULOS (PERÚ - MTC) ---
# Mapeo de clases YOLO a categorías del formato Excel
VEHICLE_CLASSES = {
    'car': 'Auto / Camioneta',
    'motorcycle': 'Moto',
    'bus': 'Bus / Micro',
    'truck': 'Camión 2E',
    'person': 'Peatón'
}

# --- CONFIGURACIÓN DE TIEMPO ---
INTERVAL_MINUTES = 15  # Intervalo estándar para aforos

# --- COLORES PARA VISUALIZACIÓN (BGR) ---
COLORS = {
    'Auto / Camioneta': (255, 0, 0),    # Azul
    'Moto': (0, 255, 255),             # Amarillo
    'Bus / Micro': (0, 165, 255),      # Naranja
    'Camión 2E': (0, 0, 255),          # Rojo
    'Peatón': (0, 255, 0),             # Verde
    'Zone': (255, 255, 255)            # Blanco
}