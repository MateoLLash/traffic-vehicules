"""
Script de inicialización del proyecto
Crea carpetas necesarias y descarga el modelo YOLO
"""

import os
import sys
from pathlib import Path

def setup_project():
    """Configura la estructura del proyecto"""
    
    print("🚀 Iniciando configuración del proyecto...")
    print("=" * 60)
    
    # Obtener directorio base
    BASE_DIR = Path(__file__).parent
    
    # Carpetas necesarias
    folders = {
        'models': BASE_DIR / 'models',
        'uploads': BASE_DIR / 'Uploads',
        'output': BASE_DIR / 'Output',
        'temp': BASE_DIR / 'temp'
    }
    
    # Crear carpetas
    print("\n📁 Creando estructura de carpetas...")
    for name, path in folders.items():
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            print(f"   ✅ Carpeta '{name}' creada: {path}")
        else:
            print(f"   ℹ️  Carpeta '{name}' ya existe: {path}")
    
    # Descargar modelo YOLO
    print("\n🤖 Descargando modelo YOLO...")
    model_path = folders['models'] / 'yolov8n.pt'
    
    if model_path.exists():
        print(f"   ℹ️  Modelo ya existe: {model_path}")
    else:
        try:
            from ultralytics import YOLO
            print("   ⏳ Descargando yolov8n.pt (aproximadamente 6 MB)...")
            model = YOLO('yolov8n.pt')
            
            # Mover el modelo a la carpeta models
            import shutil
            downloaded_model = Path('yolov8n.pt')
            if downloaded_model.exists():
                shutil.move(str(downloaded_model), str(model_path))
                print(f"   ✅ Modelo descargado: {model_path}")
            else:
                print("   ⚠️  El modelo se descargó pero no se pudo mover")
                print(f"   ℹ️  Búscalo en: {Path.cwd()}")
        
        except ImportError:
            print("   ❌ Error: ultralytics no está instalado")
            print("   💡 Ejecuta: pip install ultralytics")
            return False
        
        except Exception as e:
            print(f"   ❌ Error al descargar modelo: {str(e)}")
            print("   💡 El modelo se descargará automáticamente al ejecutar la app")
    
    # Verificar dependencias críticas
    print("\n📦 Verificando dependencias...")
    dependencies = {
        'streamlit': 'streamlit',
        'cv2': 'opencv-python',
        'ultralytics': 'ultralytics',
        'numpy': 'numpy',
        'pandas': 'pandas',
        'plotly': 'plotly'
    }
    
    missing = []
    for module, package in dependencies.items():
        try:
            __import__(module)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} - NO INSTALADO")
            missing.append(package)
    
    if missing:
        print("\n⚠️  Faltan dependencias. Instálalas con:")
        print(f"   pip install {' '.join(missing)}")
        return False
    
    # Crear archivo .gitignore
    print("\n📝 Creando .gitignore...")
    gitignore_path = BASE_DIR / '.gitignore'
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/

# Archivos del proyecto
Uploads/
Output/
temp/
*.mp4
*.avi
*.mov
*.json
*.xlsx
*.csv

# Modelos (opcional, descomentar si no quieres versionar)
# models/*.pt

# Streamlit
.streamlit/

# IDEs
.vscode/
.idea/
*.swp
*.swo
"""
    
    if not gitignore_path.exists():
        with open(gitignore_path, 'w', encoding='utf-8') as f:
            f.write(gitignore_content)
        print(f"   ✅ .gitignore creado")
    else:
        print(f"   ℹ️  .gitignore ya existe")
    
    # Resumen final
    print("\n" + "=" * 60)
    print("✅ CONFIGURACIÓN COMPLETADA")
    print("=" * 60)
    print("\n📊 Estructura del proyecto:")
    print(f"""
    {BASE_DIR.name}/
    ├── 📄 app_v2.py
    ├── 📄 counter_v2.py
    ├── 📄 detector.py
    ├── 📄 tracker.py
    ├── 📄 setup.py
    ├── 📁 models/
    │   └── 📄 yolov8n.pt
    ├── 📁 Uploads/      (videos subidos)
    ├── 📁 Output/       (resultados)
    └── 📁 temp/         (archivos temporales)
    """)
    
    print("\n🚀 Para iniciar la aplicación, ejecuta:")
    print("   streamlit run app_v2.py")
    print("\n")
    
    return True

if __name__ == "__main__":
    success = setup_project()
    sys.exit(0 if success else 1)
