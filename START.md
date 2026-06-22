# 🚀 Inicio Rápido - Traffic Analysis Tool

## Para Empezar en 3 Pasos

### 1️⃣ Instalar Dependencias (Solo primera vez)

```bash
# Activar entorno virtual
python -m venv venv

# En Windows:
venv\Scripts\activate

# En Linux/Mac:
source venv/bin/activate

# Instalar paquetes
pip install -r requirements.txt
```

⏱️ Tiempo estimado: 5-10 minutos

---

### 2️⃣ Ejecutar la Aplicación

```bash
streamlit run app.py
```

La aplicación se abrirá automáticamente en tu navegador en:
🌐 **http://localhost:8501**

---

### 3️⃣ Usar el Sistema

1. **Cargar Video** 📁
   - Click en sidebar → "Cargar Video"
   - Selecciona un archivo MP4, AVI o MOV
   
2. **Configurar Detección** 🎯
   - Ajusta umbral de confianza (recomendado: 0.5)
   - Selecciona tamaño de modelo (recomendado: 'n' para pruebas)
   - Marca las clases a detectar
   - Click en "Inicializar Detector"

3. **Definir Líneas** 📍
   - Ve a pestaña "Definir Líneas"
   - Agrega líneas de conteo usando coordenadas
   - Visualiza las líneas sobre el frame

4. **Procesar** ▶️
   - Ve a pestaña "Procesar Video"
   - Click en "Iniciar Procesamiento"
   - Espera a que termine

5. **Ver Resultados** 📊
   - Ve a pestaña "Resultados"
   - Explora estadísticas y gráficos

6. **Exportar** 📥
   - Ve a pestaña "Exportar"
   - Descarga Excel, CSV o ambos

---

## 📝 Ejemplo de Coordenadas para Líneas

### Para video 1920x1080 (Full HD)
```
Línea Horizontal (cruzar de arriba a abajo):
- Inicio X: 200
- Inicio Y: 500
- Fin X: 1700
- Fin Y: 500

Línea Vertical (cruzar de izquierda a derecha):
- Inicio X: 960
- Inicio Y: 200
- Fin X: 960
- Fin Y: 880
```

### Para video 1280x720 (HD)
```
Línea Horizontal:
- Inicio: (150, 360)
- Fin: (1130, 360)

Línea Vertical:
- Inicio: (640, 150)
- Fin: (640, 570)
```

---

## 🎬 Videos de Prueba Recomendados

Descarga videos gratuitos desde:

1. **Pexels**: https://www.pexels.com/search/videos/traffic/
2. **Pixabay**: https://pixabay.com/videos/search/cars/
3. **Videvo**: https://www.videvo.net/

Busca: "traffic", "cars", "pedestrians", "intersection"

---

## 💡 Configuraciones Recomendadas

### Para Videos con Poco Tráfico
```
Umbral de Confianza: 0.4
Modelo: n (nano)
```

### Para Videos con Tráfico Moderado
```
Umbral de Confianza: 0.5
Modelo: s (small)
```

### Para Videos con Mucho Tráfico
```
Umbral de Confianza: 0.6
Modelo: m (medium)
```

---

## ❓ ¿Problemas?

### La aplicación no inicia
```bash
# Verifica que el entorno virtual esté activado
which python  # Linux/Mac
where python  # Windows

# Debe mostrar la ruta dentro de venv/
```

### Error al importar módulos
```bash
pip install --upgrade -r requirements.txt
```

### Puerto 8501 ocupado
```bash
streamlit run app.py --server.port 8502
```

---

## 📚 Más Información

- **README.md**: Documentación completa
- **INSTALL.md**: Guía de instalación detallada
- **examples/README.md**: Guía de videos de ejemplo

---

## 🎯 Primer Uso - Checklist

- [ ] Entorno virtual creado y activado
- [ ] Dependencias instaladas (`pip install -r requirements.txt`)
- [ ] Aplicación iniciada (`streamlit run app.py`)
- [ ] Video de prueba descargado
- [ ] Video cargado en la aplicación
- [ ] Detector inicializado
- [ ] Al menos 1 línea de conteo definida
- [ ] Video procesado exitosamente
- [ ] Resultados visualizados
- [ ] Datos exportados

---

**¿Todo listo?** 🚀 ¡Comienza a analizar tráfico!

Para soporte: https://github.com/tu-usuario/traffic-analysis-tool/issues
