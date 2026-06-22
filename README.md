# 🚗 Traffic Analysis Tool

Sistema completo de análisis de tráfico vehicular y peatonal utilizando visión computacional con YOLOv8, desarrollado en Python con interfaz Streamlit.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-red.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-orange.svg)

## 📋 Tabla de Contenidos

- [Características](#-características)
- [Requisitos del Sistema](#-requisitos-del-sistema)
- [Instalación](#-instalación)
- [Guía de Uso](#-guía-de-uso)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Configuración Avanzada](#-configuración-avanzada)
- [Exportación de Datos](#-exportación-de-datos)
- [Troubleshooting](#-troubleshooting)
- [Roadmap](#-roadmap)
- [Contribuciones](#-contribuciones)
- [Licencia](#-licencia)

## ✨ Características

### 🎯 Detección y Tracking
- **Detección con YOLOv8**: Modelo pre-entrenado en COCO dataset
- **Tracking Multi-Objeto**: Sistema de seguimiento basado en IoU y distancia de centroides
- **Clases Soportadas**:
  - 🚶 Peatones (person)
  - 🚗 Automóviles (car)
  - 🏍️ Motocicletas (motorcycle)
  - 🚌 Autobuses (bus)
  - 🚚 Camiones (truck)
  - 🚲 Bicicletas (bicycle)

### 📊 Sistema de Conteo
- **Líneas de Conteo Configurables**: Define múltiples líneas de conteo sobre el video
- **Detección de Dirección**: Identifica dirección del movimiento (arriba↔abajo, izquierda↔derecha)
- **Prevención de Duplicados**: Evita contar el mismo objeto múltiples veces
- **Conteo por Categoría**: Estadísticas separadas por tipo de objeto

### 📈 Análisis y Visualizaciones
- **Gráficos de Barras**: Conteos totales por categoría
- **Series Temporales**: Flujo de tráfico a lo largo del tiempo
- **Mapas de Calor**: Zonas con mayor actividad
- **Diagramas de Flujo**: Visualización de direcciones predominantes
- **Distribución de Direcciones**: Análisis mediante gráficos de pastel

### 💾 Exportación de Datos
- **Excel Completo**:
  - Resumen general con métricas clave
  - Conteos totales y porcentajes
  - Conteos por línea y dirección
  - Detalle de cada cruce con timestamps
  - Series temporales
  - Estadísticas agregadas
  
- **CSV (Datos Crudos)**:
  - CSV de cruces completos
  - CSV de resumen estadístico
  - CSV de series temporales

- **Video Procesado**:
  - Bounding boxes con IDs de tracking
  - Líneas de conteo visibles
  - Contadores en tiempo real
  - Trayectorias de objetos

### 🖥️ Interfaz de Usuario
- **Streamlit UI**: Interfaz web intuitiva y moderna
- **Visualización en Tiempo Real**: Monitoreo del procesamiento
- **Configuración Interactiva**: Ajustes sin editar código
- **Sistema de Tabs**: Organización clara de funcionalidades

## 🔧 Requisitos del Sistema

### Hardware Mínimo
- **CPU**: Intel Core i5 o equivalente
- **RAM**: 8 GB (16 GB recomendado)
- **GPU**: NVIDIA con CUDA (opcional, pero recomendado)
- **Almacenamiento**: 5 GB libres

### Hardware Recomendado
- **CPU**: Intel Core i7 o superior
- **RAM**: 16 GB o más
- **GPU**: NVIDIA RTX 2060 o superior con 6GB VRAM
- **Almacenamiento**: 10 GB libres (SSD preferible)

### Software
- **Sistema Operativo**: Windows 10/11, Linux (Ubuntu 20.04+), macOS 10.15+
- **Python**: 3.8, 3.9, 3.10, o 3.11
- **CUDA**: 11.8+ (opcional, para aceleración GPU)

## 📥 Instalación

### Paso 1: Clonar el Repositorio

```bash
git clone https://github.com/tu-usuario/traffic-analysis-tool.git
cd traffic-analysis-tool
```

### Paso 2: Crear Entorno Virtual

**En Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**En Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Paso 3: Instalar Dependencias

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Nota**: La primera vez que ejecutes el sistema, YOLOv8 descargará automáticamente el modelo pre-entrenado (~6 MB para yolov8n).

### Paso 4: Verificar Instalación

```bash
python -c "import cv2, streamlit, ultralytics; print('✅ Instalación correcta')"
```

## 🚀 Guía de Uso

### Inicio Rápido

1. **Iniciar la aplicación**:
```bash
streamlit run app.py
```

2. La aplicación se abrirá automáticamente en tu navegador en `http://localhost:8501`

### Flujo de Trabajo Completo

#### 1️⃣ Cargar Video

1. En el **sidebar izquierdo**, haz clic en "📁 1. Cargar Video"
2. Selecciona un video en formato MP4, AVI, MOV o MKV
3. Espera a que se carguen las propiedades del video
4. Verás un resumen con:
   - Resolución del video
   - FPS (frames por segundo)
   - Duración total
   - Tiempo estimado de procesamiento

#### 2️⃣ Configurar Detección

1. **Umbral de Confianza** (0.1 - 1.0):
   - Valores bajos (0.3-0.4): Más detecciones, pero puede haber falsos positivos
   - Valores medios (0.5-0.6): Balance entre precisión y recall
   - Valores altos (0.7-0.9): Solo detecciones muy confiables

2. **Tamaño del Modelo**:
   - `n` (nano): Rápido, menor precisión - Recomendado para pruebas
   - `s` (small): Balance velocidad/precisión
   - `m` (medium): Buena precisión, requiere más recursos
   - `l` (large): Máxima precisión, más lento

3. **Seleccionar Clases**: Marca las categorías que deseas detectar

4. Haz clic en **"🔄 Inicializar Detector"**

#### 3️⃣ Definir Líneas de Conteo

1. Ve a la pestaña **"📍 Definir Líneas"**
2. Para cada línea de conteo:
   - **Nombre**: Identificador descriptivo (ej: "Entrada Principal")
   - **Coordenadas Inicio**: Punto inicial de la línea (X, Y)
   - **Coordenadas Fin**: Punto final de la línea (X, Y)
   - **Color**: Color visual de la línea
3. Haz clic en **"➕ Agregar Línea"**
4. Repite para agregar múltiples líneas
5. Las líneas se visualizarán sobre el primer frame del video

**Consejos para posicionar líneas**:
- Coloca líneas perpendiculares al flujo principal de tráfico
- Evita zonas con muchas oclusiones
- Para calles bidireccionales, usa 2 líneas (una por dirección)
- Usa el frame de referencia para identificar coordenadas exactas

#### 4️⃣ Procesar Video

1. Ve a la pestaña **"▶️ Procesar Video"**
2. Verifica que todos los requisitos estén cumplidos (✅)
3. Opciones:
   - ☑️ **Guardar video procesado**: Genera MP4 con anotaciones
   - ☑️ **Mostrar visualizaciones**: Muestra progreso en tiempo real
4. Haz clic en **"🚀 Iniciar Procesamiento"**
5. Monitorea el progreso:
   - Barra de progreso
   - Métricas en tiempo real
   - Frame actual (cada 30 frames)
   - Estadísticas actualizadas

**Tiempos de procesamiento estimados** (video 1080p@30fps):
- Con GPU: ~1-2x tiempo real
- Sin GPU: ~3-5x tiempo real

#### 5️⃣ Analizar Resultados

1. Ve a la pestaña **"📊 Resultados"**
2. Explora:
   - **Resumen General**: Métricas clave
   - **Conteos por Categoría**: Tabla y gráfico de barras
   - **Conteos por Línea**: Detalle por cada línea de conteo
   - **Detalle de Cruces**: Tabla con cada evento detectado
3. Haz clic en **"🎨 Generar Visualizaciones"** para crear gráficos

#### 6️⃣ Exportar Datos

1. Ve a la pestaña **"📥 Exportar"**
2. Opciones:
   - **📊 Exportar a Excel**: Archivo completo con todas las hojas
   - **📄 Exportar CSV**: Archivos CSV separados
   - **📦 Exportar Todo**: Genera todos los formatos
3. Los archivos se guardan en `outputs/session_YYYYMMDD_HHMMSS/exports/`
4. Descarga los archivos directamente desde la interfaz

## 📁 Estructura del Proyecto

```
traffic_analysis_tool/
├── app.py                  # Aplicación Streamlit principal
├── detector.py             # Módulo de detección YOLOv8
├── tracker.py              # Módulo de tracking multi-objeto
├── counter.py              # Sistema de conteo con líneas
├── exporter.py             # Exportación a Excel/CSV
├── visualizer.py           # Generación de gráficos
├── utils.py                # Utilidades generales
├── requirements.txt        # Dependencias Python
├── README.md               # Esta documentación
├── .gitignore              # Archivos ignorados por git
├── examples/               # Videos de ejemplo (opcional)
│   └── README.md
└── outputs/                # Directorio de salida (generado automáticamente)
    └── session_YYYYMMDD_HHMMSS/
        ├── videos/         # Videos procesados
        ├── exports/        # Archivos Excel/CSV
        ├── visualizations/ # Gráficos PNG
        └── logs/           # Archivos de log
```

## ⚙️ Configuración Avanzada

### Ajustar Parámetros del Tracker

Edita `app.py` en la línea donde se crea el tracker:

```python
st.session_state.tracker = ObjectTracker(
    max_age=10,          # Frames máximos sin actualización antes de eliminar track
    min_hits=3,          # Hits mínimos para considerar track válido
    iou_threshold=0.3,   # Umbral de IoU para asociación (0.0-1.0)
    distance_threshold=50 # Distancia máxima en píxeles para asociación
)
```

**Recomendaciones**:
- **Videos lentos/estables**: `max_age=15`, `min_hits=5`
- **Videos rápidos/inestables**: `max_age=5`, `min_hits=2`
- **Objetos grandes**: `distance_threshold=100`
- **Objetos pequeños**: `distance_threshold=30`

### Cambiar Intervalo de Series Temporales

En `counter.py`, método `get_time_series_data`:

```python
time_series = counter.get_time_series_data(interval_seconds=60)  # 60 segundos por defecto
```

### Personalizar Colores por Clase

Edita `utils.py`, diccionario `OBJECT_CLASSES`:

```python
OBJECT_CLASSES = {
    'person': {'name': 'Peatón', 'color': (255, 0, 0), 'category': 'pedestrian'},
    'car': {'name': 'Auto', 'color': (0, 255, 0), 'category': 'vehicle'},
    # ... más clases
}
```

### Usar Modelo Personalizado

Si tienes un modelo YOLOv8 entrenado:

```python
detector = ObjectDetector(
    model_name='path/to/your/model.pt',  # Tu modelo personalizado
    confidence_threshold=0.5,
    target_classes=['car', 'person']
)
```

## 📊 Exportación de Datos

### Formato Excel

El archivo Excel incluye las siguientes hojas:

1. **Resumen**: Métricas generales del análisis
2. **Conteos Totales**: Tabla con conteos y porcentajes por categoría
3. **Conteos por Línea**: Conteos separados por cada línea con direcciones
4. **Detalle de Cruces**: Registro completo de cada cruce con timestamps
5. **Series Temporales**: Datos temporales por intervalos
6. **Estadísticas Dirección**: Conteos agregados por dirección

### Formato CSV

Se generan 3 archivos CSV:

1. **cruces_raw_TIMESTAMP.csv**: Datos crudos de todos los cruces
2. **resumen_TIMESTAMP.csv**: Resumen estadístico por categoría
3. **series_temporales_TIMESTAMP.csv**: Datos de series temporales

### Video Procesado

El video procesado incluye:
- Bounding boxes de color por clase
- IDs de tracking únicos
- Trayectorias de movimiento
- Líneas de conteo con contadores en vivo
- Centroide de cada objeto

## 🔍 Troubleshooting

### Problema: Error al cargar modelo YOLO

**Síntomas**: 
```
Error: Failed to load model yolov8n.pt
```

**Soluciones**:
1. Verificar conexión a internet (primera ejecución descarga el modelo)
2. Descargar modelo manualmente desde [Ultralytics](https://github.com/ultralytics/assets/releases)
3. Verificar espacio en disco

### Problema: Procesamiento muy lento

**Síntomas**: FPS < 5 durante procesamiento

**Soluciones**:
1. Usar modelo más pequeño (`yolov8n` en lugar de `yolov8l`)
2. Reducir resolución del video antes de procesar
3. Desactivar "Guardar video procesado"
4. Cerrar otras aplicaciones
5. Si tienes GPU NVIDIA, instalar CUDA y cuDNN

### Problema: Muchos falsos positivos

**Síntomas**: Objetos incorrectos detectados

**Soluciones**:
1. Aumentar umbral de confianza (0.6-0.7)
2. Filtrar clases no deseadas
3. Ajustar `min_hits` del tracker a valores más altos

### Problema: Objetos no detectados

**Síntomas**: Objetos visibles no son contados

**Soluciones**:
1. Reducir umbral de confianza (0.3-0.4)
2. Verificar que la clase esté en la lista de clases seleccionadas
3. Mejorar iluminación/calidad del video
4. Reducir `min_hits` del tracker

### Problema: Conteos duplicados

**Síntomas**: Mismo objeto contado múltiples veces

**Soluciones**:
1. Verificar posición de líneas de conteo
2. Aumentar `max_age` del tracker
3. Ajustar `iou_threshold` a valores más bajos (0.2)

### Problema: Error "Out of Memory"

**Síntomas**:
```
CUDA out of memory
```

**Soluciones**:
1. Usar modelo más pequeño (`yolov8n`)
2. Procesar videos en resolución menor
3. Cerrar otras aplicaciones que usen GPU
4. Reducir batch size (si se modifica el código)

## 🗺️ Roadmap

### Versión 1.1 (Próxima)
- [ ] Soporte para procesamiento en batch de múltiples videos
- [ ] Zonas de interés (ROI) configurables
- [ ] Detección de eventos especiales (paradas, giros, adelantamientos)
- [ ] Exportación a formato JSON

### Versión 1.2
- [ ] Dashboard web con histórico de análisis
- [ ] API REST para integración con otros sistemas
- [ ] Análisis de velocidad de vehículos
- [ ] Clasificación de vehículos por subtipo

### Versión 2.0 (Migración a Web)
- [ ] Interfaz web multi-usuario
- [ ] Procesamiento en la nube
- [ ] Análisis en tiempo real con cámaras IP
- [ ] Base de datos para almacenamiento persistente
- [ ] Sistema de usuarios y autenticación
- [ ] Reportes automatizados por email

## 🤝 Contribuciones

¡Las contribuciones son bienvenidas! Para contribuir:

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

### Guías de Contribución

- Sigue el estilo de código PEP 8
- Agrega docstrings a todas las funciones
- Incluye pruebas para nuevas funcionalidades
- Actualiza la documentación según sea necesario

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver archivo `LICENSE` para más detalles.

## 👥 Autores

- **Tu Nombre** - *Desarrollo Inicial* - [GitHub](https://github.com/tu-usuario)

## 🙏 Agradecimientos

- [Ultralytics](https://ultralytics.com/) por YOLOv8
- [Streamlit](https://streamlit.io/) por el framework de UI
- Comunidad de OpenCV y Computer Vision

## 📞 Soporte

- **Issues**: [GitHub Issues](https://github.com/tu-usuario/traffic-analysis-tool/issues)
- **Email**: tu-email@example.com
- **Documentación**: [Wiki](https://github.com/tu-usuario/traffic-analysis-tool/wiki)

---

**¿Te ha sido útil este proyecto?** ¡Dale una ⭐ en GitHub!

Hecho con ❤️ usando Python, YOLOv8 y Streamlit
