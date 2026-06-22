# 📹 Videos de Ejemplo

Esta carpeta está destinada para almacenar videos de ejemplo que puedes usar para probar el sistema de análisis de tráfico.

## 🎬 Videos Recomendados

### Características Ideales
- **Resolución**: 720p (1280x720) o 1080p (1920x1080)
- **FPS**: 25-30 fps
- **Duración**: 30 segundos - 5 minutos (para pruebas)
- **Formato**: MP4, AVI, MOV
- **Iluminación**: Buena iluminación, preferiblemente luz natural
- **Ángulo**: Vista superior o semi-superior (45°)
- **Contenido**: Tráfico vehicular y/o peatonal claramente visible

### Fuentes de Videos Gratuitos

1. **Pexels Videos** (https://www.pexels.com/videos/)
   - Buscar: "traffic", "cars", "pedestrians", "street"
   - Licencia gratuita para uso personal y comercial

2. **Pixabay** (https://pixabay.com/videos/)
   - Gran colección de videos de tráfico
   - Licencia libre de derechos

3. **Videvo** (https://www.videvo.net/)
   - Videos HD de tráfico urbano
   - Algunos gratuitos con atribución

4. **YouTube** (con permisos apropiados)
   - Videos de cámaras de tráfico
   - Asegúrate de tener permiso para uso

## 📥 Cómo Agregar Videos

### Opción 1: Descarga Manual
1. Descarga videos desde las fuentes recomendadas
2. Guarda los archivos en esta carpeta (`examples/`)
3. Nombra los archivos descriptivamente:
   ```
   traffic_highway_daytime.mp4
   pedestrian_crossing_afternoon.mp4
   intersection_rush_hour.mp4
   ```

### Opción 2: Tus Propios Videos
- Puedes grabar tus propios videos con tu smartphone
- Recomendaciones:
  - Mantén la cámara estable (usa trípode si es posible)
  - Graba desde una posición elevada
  - Evita movimientos bruscos de cámara
  - Asegura buena iluminación

## 🎯 Escenarios de Prueba Sugeridos

### Básico
```
examples/
├── basic_traffic.mp4        # Tráfico simple con pocos vehículos
└── pedestrian_simple.mp4    # Peatones cruzando calle
```

### Intermedio
```
examples/
├── intersection_2way.mp4    # Intersección de 2 vías
├── mixed_traffic.mp4        # Mezcla de vehículos y peatones
└── highway_traffic.mp4      # Tráfico de autopista
```

### Avanzado
```
examples/
├── rush_hour_complex.mp4    # Hora pico con mucho tráfico
├── night_traffic.mp4        # Tráfico nocturno
└── weather_rain.mp4         # Condiciones climáticas adversas
```

## ⚙️ Configuraciones Recomendadas por Escenario

### Tráfico Ligero (Pocos Objetos)
```python
Umbral de Confianza: 0.5
Tamaño de Modelo: n (nano)
min_hits: 2
max_age: 10
```

### Tráfico Moderado
```python
Umbral de Confianza: 0.5
Tamaño de Modelo: s (small)
min_hits: 3
max_age: 8
```

### Tráfico Denso (Muchos Objetos)
```python
Umbral de Confianza: 0.6
Tamaño de Modelo: m (medium)
min_hits: 4
max_age: 5
```

### Condiciones Difíciles (Noche/Lluvia)
```python
Umbral de Confianza: 0.4
Tamaño de Modelo: m o l
min_hits: 2
max_age: 12
```

## 📊 Ejemplos de Líneas de Conteo

### Para Calle Simple (Tráfico Unidireccional)
```
Línea 1: "Entrada"
- Inicio: (100, 400)
- Fin: (900, 400)
- Color: Verde
```

### Para Intersección
```
Línea 1: "Norte-Sur"
- Inicio: (500, 100)
- Fin: (500, 700)
- Color: Verde

Línea 2: "Este-Oeste"
- Inicio: (100, 400)
- Fin: (900, 400)
- Color: Azul
```

### Para Cruce Peatonal
```
Línea 1: "Cruce Principal"
- Inicio: (300, 500)
- Fin: (700, 500)
- Color: Rojo
```

## 🚫 Videos NO Recomendados

Evita videos con:
- ❌ Movimiento excesivo de cámara
- ❌ Zoom in/out constante
- ❌ Objetos muy pequeños (< 20 píxeles)
- ❌ Muy baja resolución (< 480p)
- ❌ FPS muy bajo (< 15 fps)
- ❌ Oclusiones severas constantes
- ❌ Ángulos muy oblicuos

## 💡 Tips para Mejores Resultados

1. **Estabilidad**: Videos estables dan mejores resultados de tracking
2. **Resolución**: Mayor resolución = mejor detección de objetos pequeños
3. **Iluminación**: Luz uniforme mejora la detección
4. **Duración**: Para pruebas iniciales, usa videos cortos (< 2 min)
5. **Calidad**: Evita videos muy comprimidos o con artefactos

## 📝 Plantilla de Metadatos

Crea un archivo `video_info.txt` con información de tus videos:

```
Nombre: traffic_highway_daytime.mp4
Resolución: 1920x1080
FPS: 30
Duración: 120 segundos
Escena: Autopista urbana durante el día
Objetos principales: Autos, camiones, motos
Dificultad: Moderada
Notas: Buena iluminación, tráfico fluido
```

## 🔗 Enlaces Útiles

- [Pexels Videos - Traffic](https://www.pexels.com/search/videos/traffic/)
- [Pixabay - Street Videos](https://pixabay.com/videos/search/street/)
- [Guía de YOLOv8](https://docs.ultralytics.com/)
- [Tutoriales de Computer Vision](https://learnopencv.com/)

---

**Nota**: Los videos de ejemplo NO están incluidos en el repositorio por razones de tamaño. Descárgalos según las instrucciones anteriores.
