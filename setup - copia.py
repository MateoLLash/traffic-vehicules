# verificar_setup.py
import os
from pathlib import Path

def verificar():
    print("🔍 Verificando configuración del proyecto...\n")
    
    # Verificar carpetas
    carpetas = ['models', 'Uploads', 'Output', 'temp']
    print("📁 Carpetas:")
    for carpeta in carpetas:
        existe = Path(carpeta).exists()
        icono = "✅" if existe else "❌"
        print(f"   {icono} {carpeta}/")
    
    # Verificar modelo
    print("\n🤖 Modelo YOLO:")
    modelo = Path('models/yolov8n.pt')
    if modelo.exists():
        size_mb = modelo.stat().st_size / (1024 * 1024)
        print(f"   ✅ yolov8n.pt ({size_mb:.2f} MB)")
    else:
        print(f"   ❌ yolov8n.pt NO ENCONTRADO")
    
    # Verificar archivos Python
    print("\n📄 Archivos principales:")
    archivos = ['app_v2.py', 'counter_v2.py', 'detector.py', 'tracker.py']
    for archivo in archivos:
        existe = Path(archivo).exists()
        icono = "✅" if existe else "❌"
        print(f"   {icono} {archivo}")
    
    # Verificar dependencias
    print("\n📦 Dependencias:")
    modulos = {
        'streamlit': 'streamlit',
        'cv2': 'opencv-python',
        'ultralytics': 'ultralytics',
        'numpy': 'numpy',
        'pandas': 'pandas',
        'plotly': 'plotly'
    }
    
    for modulo, paquete in modulos.items():
        try:
            __import__(modulo)
            print(f"   ✅ {paquete}")
        except ImportError:
            print(f"   ❌ {paquete} - Instalar con: pip install {paquete}")
    
    print("\n" + "="*50)
    print("✅ Verificación completada")
    print("="*50)

if __name__ == "__main__":
    verificar()
