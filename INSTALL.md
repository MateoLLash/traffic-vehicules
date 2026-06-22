# 📦 Guía de Instalación Detallada

## Tabla de Contenidos
1. [Requisitos Previos](#requisitos-previos)
2. [Instalación en Windows](#instalación-en-windows)
3. [Instalación en Linux](#instalación-en-linux)
4. [Instalación en macOS](#instalación-en-macos)
5. [Configuración de GPU (Opcional)](#configuración-de-gpu)
6. [Verificación de Instalación](#verificación)
7. [Problemas Comunes](#problemas-comunes)

## Requisitos Previos

### Todos los Sistemas Operativos
- Python 3.8 o superior
- pip actualizado
- Git (para clonar el repositorio)
- 5 GB de espacio libre en disco
- Conexión a internet (para descargar modelos)

## Instalación en Windows

### Paso 1: Instalar Python

1. Descarga Python desde [python.org](https://www.python.org/downloads/)
2. Durante la instalación:
   - ✅ Marca "Add Python to PATH"
   - ✅ Marca "Install pip"
3. Verifica la instalación:
   ```cmd
   python --version
   pip --version
   ```

### Paso 2: Clonar el Repositorio

```cmd
git clone https://github.com/tu-usuario/traffic-analysis-tool.git
cd traffic-analysis-tool
```

### Paso 3: Crear Entorno Virtual

```cmd
python -m venv venv
venv\Scripts\activate
```

Deberías ver `(venv)` al inicio de tu línea de comandos.

### Paso 4: Instalar Dependencias

```cmd
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**Nota**: La instalación puede tomar 5-10 minutos dependiendo de tu conexión.

### Paso 5: Ejecutar la Aplicación

```cmd
streamlit run app.py
```

La aplicación se abrirá en `http://localhost:8501`

## Instalación en Linux

### Ubuntu/Debian

#### Paso 1: Actualizar Sistema

```bash
sudo apt update
sudo apt upgrade -y
```

#### Paso 2: Instalar Python y Dependencias del Sistema

```bash
sudo apt install -y python3 python3-pip python3-venv git
sudo apt install -y libgl1-mesa-glx libglib2.0-0  # Para OpenCV
```

#### Paso 3: Clonar Repositorio

```bash
git clone https://github.com/tu-usuario/traffic-analysis-tool.git
cd traffic-analysis-tool
```

#### Paso 4: Crear Entorno Virtual

```bash
python3 -m venv venv
source venv/bin/activate
```

#### Paso 5: Instalar Dependencias Python

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### Paso 6: Ejecutar

```bash
streamlit run app.py
```

### Fedora/RHEL/CentOS

```bash
sudo dnf install -y python3 python3-pip git mesa-libGL
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

## Instalación en macOS

### Paso 1: Instalar Homebrew (si no está instalado)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Paso 2: Instalar Python

```bash
brew install python@3.10
```

### Paso 3: Clonar y Configurar

```bash
git clone https://github.com/tu-usuario/traffic-analysis-tool.git
cd traffic-analysis-tool
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Paso 4: Ejecutar

```bash
streamlit run app.py
```

## Configuración de GPU

### NVIDIA GPU (Windows/Linux)

Para aprovechar aceleración GPU con CUDA:

#### Paso 1: Verificar GPU Compatible

```bash
nvidia-smi
```

#### Paso 2: Instalar CUDA Toolkit

- Windows: [Descarga CUDA](https://developer.nvidia.com/cuda-downloads)
- Linux: 
  ```bash
  # Ubuntu
  wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/cuda-ubuntu2004.pin
  sudo mv cuda-ubuntu2004.pin /etc/apt/preferences.d/cuda-repository-pin-600
  sudo apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/3bf863cc.pub
  sudo add-apt-repository "deb https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/ /"
  sudo apt update
  sudo apt install cuda
  ```

#### Paso 3: Instalar PyTorch con CUDA

```bash
pip uninstall torch torchvision  # Remover versión CPU
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

#### Paso 4: Verificar

```python
import torch
print(torch.cuda.is_available())  # Debe retornar True
print(torch.cuda.get_device_name(0))  # Nombre de tu GPU
```

### Apple Silicon (M1/M2/M3)

```bash
pip install torch torchvision torchaudio
```

PyTorch usará automáticamente Metal Performance Shaders (MPS).

## Verificación

### Test Rápido

```bash
python -c "import cv2, streamlit, ultralytics, torch; print('✅ Todo OK')"
```

### Test Completo

```bash
# Activar entorno virtual primero
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Ejecutar tests de cada módulo
python detector.py
python tracker.py
python counter.py
python exporter.py
python visualizer.py
```

Cada módulo debería imprimir "✓ Módulo XXX funcionando correctamente".

## Problemas Comunes

### Error: "No module named 'cv2'"

**Solución**:
```bash
pip uninstall opencv-python opencv-contrib-python
pip install opencv-python==4.9.0.80
```

### Error: "ModuleNotFoundError: No module named 'ultralytics'"

**Solución**:
```bash
pip install ultralytics==8.1.0
```

### Error: "DLL load failed" (Windows)

**Solución**:
1. Instala Visual C++ Redistributable:
   - [VC++ 2015-2022 x64](https://aka.ms/vs/17/release/vc_redist.x64.exe)
2. Reinicia tu PC

### Error: "Permission denied" (Linux/Mac)

**Solución**:
```bash
sudo chown -R $USER:$USER ~/traffic-analysis-tool
chmod +x app.py
```

### Error: "Port 8501 already in use"

**Solución**:
```bash
streamlit run app.py --server.port 8502
```

### Error de Memoria: "CUDA out of memory"

**Solución**:
1. Usa modelo más pequeño (yolov8n en lugar de yolov8l)
2. Reduce resolución del video
3. Cierra otras aplicaciones

### Streamlit no abre el navegador automáticamente

**Solución**:
Abre manualmente: `http://localhost:8501`

## Desinstalación

```bash
# Desactivar entorno virtual
deactivate

# Eliminar carpeta del proyecto
cd ..
rm -rf traffic-analysis-tool  # Linux/Mac
rmdir /s traffic-analysis-tool  # Windows
```

## Actualización

```bash
cd traffic-analysis-tool
git pull origin main
source venv/bin/activate  # o venv\Scripts\activate en Windows
pip install --upgrade -r requirements.txt
```

## Soporte

Si encuentras problemas:
1. Revisa la sección de [Troubleshooting](README.md#troubleshooting) en el README
2. Busca en [Issues](https://github.com/tu-usuario/traffic-analysis-tool/issues)
3. Crea un nuevo issue con:
   - Sistema operativo y versión
   - Versión de Python
   - Mensaje de error completo
   - Pasos para reproducir el problema

---

¡Listo! Ahora puedes comenzar a usar Traffic Analysis Tool. 🚀