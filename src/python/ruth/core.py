import os
import sys
import win32com.client # <--- Usamos el cliente COM directo de Windows
from . import ruth_backend 

class RuthAssistant:
    def __init__(self):
        self.name = "Ruth"
        self.version = "0.4 (SAPI Native)" 
        
        # --- NUEVA CONFIGURACIÓN DE VOZ (SAPI DIRECTO) ---
        try:
            # Invocamos al espíritu de Windows directamente
            self.speaker = win32com.client.Dispatch("SAPI.SpVoice")
            self.speaker.Volume = 100  # 0 a 100
            self.speaker.Rate = 1      # -10 a 10 (1 es velocidad normal)
            
            # Buscamos a Sabina (o cualquier voz en español México)
            voices = self.speaker.GetVoices()
            for voice in voices:
                desc = voice.GetDescription()
                # print(f"Voz detectada: {desc}") # Descomenta si quieres verlas
                if "mexico" in desc.lower() or "sabina" in desc.lower():
                    self.speaker.Voice = voice
                    break
        except Exception as e:
            print(f"⚠️ Error inicializando voz SAPI: {e}")
            self.speaker = None
        # --- FIN CONFIGURACIÓN ---

        self.system_info = self._load_system_info()
    
    def _load_system_info(self):
        try:
            return ruth_backend.get_system_info()
        except Exception as e:
            print(f"⚠️ Error cargando motor C++: {e}")
            return {"pc_name": "Unknown", "user": "Guest"}

    def speak(self, text):
        """El método que le da voz a Ruth (Versión Estable)"""
        print(f"🗣️ RUTH: {text}") 
        if self.speaker:
            # El Flag 1 (SVSFlagsAsync) permite que hable sin congelar TODO el programa,
            # pero para narrar acciones, a veces preferimos que termine de hablar antes de actuar.
            # Por ahora lo dejaremos síncrono (sin flags) para asegurar que narre.
            try:
                self.speaker.Speak(text)
            except:
                pass

    def introduce_self(self):
        intro_text = f"Atención Buzz Layllir, adelante Buzz Layllir, aquí comando estelar. Sistemas en línea. Hola Inge. Soy Ruth, tu primer modelo de asistente virtual e inteligencia artificial, estoy a tu servicio. Conectada a {self.system_info['pc_name']}."

        self.speak(intro_text)

    # ACTUALIZAMOS EXECUTE_APP PARA QUE SEA MÁS NATURAL
    def execute_app(self, app_name, args=""):
        self.speak(f"Abriendo {app_name}")
        
        # Parche CMD
        if "notepad" in app_name.lower():
            target = "cmd.exe"
            arguments = "/c start notepad"
        else:
            target = app_name
            arguments = args
            
        success = ruth_backend.run_process(target, arguments)
        return success

    # --- NUEVA HABILIDAD: TERMINAR PROCESOS ---
    def kill_app(self, app_name):
        """Mata un proceso por su nombre. Ej: 'notepad.exe'"""
        self.speak(f"Deteniendo el proceso {app_name}")
        
        # Le añadimos .exe si el usuario lo olvidó
        if not app_name.endswith(".exe"):
            app_name += ".exe"
            
        count = ruth_backend.kill_process_by_name(app_name)
        
        if count > 0:
            self.speak(f"He eliminado {count} instancias de {app_name}.")
            return True
        else:
            self.speak(f"No encontré ningún proceso llamado {app_name}.")
            return False
        
    # --- NUEVA HABILIDAD: CHEQUEO DE SALUD ---
    def check_vitals(self):
        """Analiza RAM y Disco y da un reporte verbal"""
        self.speak("Analizando signos vitales del sistema...")
        
        # 1. Chequeo de RAM
        ram = ruth_backend.get_memory_status()
        self.speak(f"Uso de memoria RAM al {ram['percent_used']} por ciento.")
        
        # Lógica inteligente: Si la RAM está muy llena, da una alerta
        if ram['percent_used'] > 85:
            self.speak("⚠️ Inge: La memoria está saturada. Recomiendo cerrar aplicaciones.")
        
        # 2. Chequeo de Disco
        disk = ruth_backend.get_disk_status()
        # Redondeamos a 2 decimales para que no diga números infinitos
        free_gb = round(disk['free_gb'], 2)
        
        self.speak(f"Espacio libre en disco C: {free_gb} Gigabytes.")
        
        if disk['free_gb'] < 10.0:
            self.speak("⚠️ Crítico Inge: Queda muy poco espacio en disco.")
        else:
            self.speak("Inge Almacenamiento en niveles óptimos.")

    def inspect_downloads(self):
        """Revisa la carpeta de descargas del usuario"""
        self.speak("Inspeccionando carpeta de Descargas...")
        
        # Truco para obtener la ruta real de Descargas en cualquier Windows
        downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
        
        # Usamos el C++ para escanear rápido
        files = ruth_backend.scan_directory(downloads_path)
        
        count = len(files)
        self.speak(f"He encontrado {count} archivos en tu carpeta de descargas.")
        
        if count > 20:
            self.speak("Tienes demasiados archivos acumulados. Deberíamos hacer limpieza pronto, Inge.")
        else:
            self.speak("Tu carpeta está bastante ordenada. ¡Bien hecho!")
            
        # Opcional: Imprimir los primeros 5 archivos para ver que funciona
        print(f"📂 Archivos detectados (Top 5): {files[:5]}")# Puedes añadir más métodos y habilidades aquí      

