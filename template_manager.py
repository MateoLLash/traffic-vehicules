import json
import os
from config import TEMPLATES_DIR

class TemplateManager:
    @staticmethod
    def save_template(name, config_data):
        """Guarda la configuración de zonas/líneas en un archivo JSON."""
        file_path = os.path.join(TEMPLATES_DIR, f"{name}.json")
        try:
            with open(file_path, 'w') as f:
                json.dump(config_data, f, indent=4)
            return True, f"Plantilla '{name}' guardada con éxito."
        except Exception as e:
            return False, f"Error al guardar plantilla: {str(e)}"

    @staticmethod
    def load_template(name):
        """Carga una configuración guardada."""
        file_path = os.path.join(TEMPLATES_DIR, f"{name}.json")
        if not os.path.exists(file_path):
            return None, "La plantilla no existe."
        try:
            with open(file_path, 'r') as f:
                return json.load(f), "Plantilla cargada."
        except Exception as e:
            return None, f"Error al cargar: {str(e)}"

    @staticmethod
    def list_templates():
        """Lista todas las plantillas disponibles."""
        return [f.replace(".json", "") for f in os.listdir(TEMPLATES_DIR) if f.endswith(".json")]