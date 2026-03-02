import os
import pyautogui
from PIL import Image
import io
import ollama
from ruth.settings import Config # 1. Invocamos la matriz

class RuthEyes:
    def __init__(self):
        # 2. Instanciamos la configuración
        config = Config()
        
        # 3. Extraemos el modelo visual (si el yaml falla, usa llava por seguridad)
        self.model = config.get("ai.vision_model", "llava")
        
        # Ruta temporal para guardar lo que ve
        self.screenshot_path = os.path.join(os.getcwd(), "temp_vision.png")

    def capture_screen(self):
        """Captura lo que hay en el monitor principal"""
        try:
            # Tomamos la foto
            screenshot = pyautogui.screenshot()
            # La guardamos temporalmente (Ollama necesita el archivo o bytes)
            screenshot.save(self.screenshot_path)
            return self.screenshot_path
        except Exception as e:
            print(f"Error visual: {e}")
            return None

    def analyze_screen(self, prompt="Describe detalladamente qué hay en esta imagen."):
        """Mira la pantalla y responde a la pregunta del usuario"""
        image_path = self.capture_screen()
        
        if not image_path:
            return "No pude abrir mis ojos (Error de captura)."

        try:
            print("👁️ RUTH MIRANDO PANTALLA...", end="", flush=True)
            
            # Enviamos la imagen + la pregunta a LLaVA
            response = ollama.chat(
                model=self.model,
                messages=[
                    {
                        'role': 'user',
                        'content': prompt,
                        'images': [image_path] # <--- Aquí va la "luz"
                    }
                ]
            )
            
            print(" (Análisis completado)")
            # Limpieza (opcional, borramos la foto temporal)
            # os.remove(self.screenshot_path) 
            
            return response['message']['content']
            
        except Exception as e:
            return f"Mi corteza visual falló: {e}"