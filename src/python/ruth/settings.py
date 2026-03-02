import os
import yaml

class Config:
    _instance = None
    _config_data = None

    def __new__(cls):
        # Implementamos un patrón Singleton: 
        # Asegura que la configuración se lea del disco solo UNA vez para ahorrar RAM.
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        # Recalibración espacial: 
        # __file__ es 'settings.py'. 
        # 1er dirname nos lleva a la carpeta 'ruth'. 
        # 2do dirname nos lleva a la carpeta 'python', donde ahora vive config.yaml.
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(base_dir, "config.yaml")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                self._config_data = yaml.safe_load(file)
                print("⚙️ Matriz de parámetros cargada exitosamente.") # Pequeño log de éxito
        except Exception as e:
            print(f"⚠️ ERROR CRÍTICO: No se pudo leer config.yaml en {config_path}. {e}")
            self._config_data = {}

    def get(self, key_path, default=None):
        """
        Permite buscar valores anidados, ej: config.get('ai.text_model')
        """
        keys = key_path.split('.')
        val = self._config_data
        try:
            for key in keys:
                val = val[key]
            return val
        except (KeyError, TypeError):
            return default