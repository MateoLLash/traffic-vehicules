# Changelog

Todos los cambios notables en este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [1.0.0] - 2026-02-16

### ✨ Añadido
- Sistema completo de detección de objetos con YOLOv8
- Tracking multi-objeto con algoritmo basado en IoU
- Sistema de conteo con líneas configurables
- Detección de dirección de movimiento (4 direcciones)
- Interfaz Streamlit completa con 4 tabs principales
- Exportación a Excel con múltiples hojas
- Exportación a CSV (datos crudos)
- Generación automática de visualizaciones:
  - Gráficos de barras
  - Series temporales
  - Mapas de calor
  - Diagramas de flujo
  - Gráficos de pastel de direcciones
- Video procesado con anotaciones
- Sistema de logging completo
- Prevención de conteos duplicados
- Soporte para 6 categorías de objetos
- Configuración de umbral de confianza
- Selección de tamaño de modelo (n, s, m, l)
- Filtrado de clases a detectar
- Visualización en tiempo real durante procesamiento
- Métricas actualizadas en vivo
- Cálculo de promedios por minuto
- Análisis de series temporales
- Documentación completa en español
- README con guía de uso detallada
- Guía de instalación paso a paso
- Ejemplos y casos de uso

### 🔧 Técnico
- Arquitectura modular (7 módulos principales)
- Manejo robusto de errores
- Validación de archivos de video
- Estimación de tiempo de procesamiento
- Sistema de estado con Streamlit session_state
- Utilidades auxiliares reutilizables
- Formato Excel con estilos
- Colores diferenciados por clase
- Sistema de coordenadas para líneas de conteo

### 📦 Dependencias
- ultralytics==8.1.0 (YOLOv8)
- opencv-python==4.9.0.80
- streamlit==1.30.0
- pandas==2.1.4
- matplotlib==3.8.2
- openpyxl==3.1.2
- Y más... (ver requirements.txt)

### 📝 Documentación
- README.md principal
- INSTALL.md con guía detallada
- examples/README.md con instrucciones
- Docstrings en todos los módulos
- Comentarios explicativos en español

### 🎯 Características Destacadas
- **Fácil de usar**: Interfaz intuitiva sin necesidad de código
- **Modular**: Cada componente es independiente y reutilizable
- **Exportable**: Múltiples formatos de salida
- **Visual**: Gráficos y visualizaciones automáticas
- **Configurable**: Ajustes sin modificar código
- **Local**: Sin necesidad de conexión constante
- **Gratuito**: Todas las dependencias son open source

### 🚀 Rendimiento
- Procesamiento: ~1-2x tiempo real con GPU
- Procesamiento: ~3-5x tiempo real sin GPU
- Modelos optimizados (nano, small, medium, large)
- Tracking eficiente con Hungarian algorithm

---

## [Unreleased]

### Planeado para 1.1
- Procesamiento en batch de múltiples videos
- Zonas de interés (ROI) configurables
- Detección de eventos especiales
- Exportación a JSON
- Modo de prueba con video de ejemplo

### Planeado para 1.2
- Dashboard con histórico
- API REST
- Análisis de velocidad
- Clasificación por subtipo de vehículo

### Planeado para 2.0
- Migración a aplicación web multi-usuario
- Procesamiento en tiempo real
- Base de datos persistente
- Sistema de autenticación
- Reportes automatizados

---

[1.0.0]: https://github.com/tu-usuario/traffic-analysis-tool/releases/tag/v1.0.0