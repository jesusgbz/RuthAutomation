# Importamos nuestra nueva Matriz
from ruth.settings import Config # <--- Importamos la clase Config para acceder a la configuración global
# --- LA MAGIA T-SYSTEMS PARA CHROME ---
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
# IMPORTS PARA AUTOMATIZACIÓN WEB
from selenium import webdriver

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys # <--- NUEVO

import time 
import os
import sys
import win32com.client
import logging
import pyautogui 
import urllib.parse # <--- AGREGAR ESTE IMPORT AL INICIO (Nativo de Python)
import speedtest
import random
from dotenv import load_dotenv

from datetime import datetime 
from . import ruth_backend 
import json
import logging
from logging.handlers import RotatingFileHandler

load_dotenv()

class RuthAssistant:
    def __init__(self):
        self.name = "Ruth" # Nombre del asistente, puedes cambiarlo si quieres
        self.version = "0.7 (Full Logger)" 
        self.browser = None # Para controlar el navegador desde cualquier método

        # --- CONFIGURACIÓN DE LOGGING (NIVEL ENTERPRISE) ---
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        log_dir = os.path.join(base_dir, "logs")
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        # El archivo ahora es un .jsonl (JSON Lines)
        log_file = os.path.join(log_dir, "ruth_system.jsonl")
        
        # 1. Obtenemos el Logger Raíz
        root_logger = logging.getLogger()
        if root_logger.hasHandlers():
            root_logger.handlers.clear() # Limpiamos configuraciones viejas
            
        root_logger.setLevel(logging.INFO)
        
        # 2. El Rotador: Máximo 5MB por archivo, conserva los últimos 3
        handler = RotatingFileHandler(
            log_file, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8'
        )
        
        # 3. El Formateador JSON
        class JsonFormatter(logging.Formatter):
            def format(self, record):
                # Estructuramos la anatomía del log
                log_record = {
                    "timestamp": self.formatTime(record, self.datefmt),
                    "level": record.levelname,
                    "module": record.module,
                    "message": record.getMessage()
                }
                # ensure_ascii=False permite que los acentos se guarden bien
                return json.dumps(log_record, ensure_ascii=False)
                
        handler.setFormatter(JsonFormatter())
        root_logger.addHandler(handler)
        
        
        self.log(f"--- INICIANDO SISTEMA RUTH v{self.version} ---")
        # --------------------------------
        
        
        # --- CONFIGURACIÓN DE VOZ (SAPI + MATRIZ) ---
        try:
            config = Config() # Invocamos la Matriz
            
            self.speaker = win32com.client.Dispatch("SAPI.SpVoice")
            
            # 1. Extraemos los valores del config.yaml
            gender_pref = config.get("voice.gender", "male").lower()
            sapi_rate = config.get("voice.rate", 2)
            sapi_vol = config.get("voice.volume", 100)
            
            # Aplicamos valores
            self.speaker.Volume = sapi_vol  
            self.speaker.Rate = sapi_rate      
            
            # 2. Búsqueda Dinámica de Identidad Vocal
            voices = self.speaker.GetVoices()
            voice_found = False

            print("\n--- VOCES DETECTADAS POR SAPI ---")
            for voice in voices:
                desc = voice.GetDescription().lower()
                print(f"- {desc}") # <--- ESTO NOS REVELARÁ LA VERDAD
            print("---------------------------------\n")
            
            for voice in voices:
                desc = voice.GetDescription().lower()
                
                # Identificamos voces femeninas en español
                if gender_pref == "female" and ("sabina" in desc):
                    self.speaker.Voice = voice
                    voice_found = True
                    self.log(f"Voz femenina configurada: {desc}")
                    break
                # Identificamos voces masculinas en español
                elif gender_pref == "male" and ("raul" in desc):
                    self.speaker.Voice = voice
                    voice_found = True
                    self.log(f"Voz masculina configurada: {desc}")
                    break
            
            if not voice_found:
                self.log(f"Alerta: Voz {gender_pref} no encontrada, usando predeterminada de Windows.", level="warning")

        except Exception as e:
            self.log(f"Error SAPI crítico: {e}", level="error")
            self.speaker = None

        self.system_info = self._load_system_info()

    
    
    
    def log(self, message, level="info"):
        """Escribe en consola Y en el archivo al mismo tiempo"""
        # Feedback visual en consola con iconos
        icon = "📝"
        if level == "error": icon = "❌"
        elif level == "warning": icon = "⚠️"
        
        print(f"{icon} {message}") 
        
        if level == "info":
            logging.info(message)
        elif level == "error":
            logging.error(message)
        elif level == "warning":
            logging.warning(message)

    def _load_system_info(self):
        try:
            info = ruth_backend.get_system_info()
            self.log(f"Sistema cargado: {info['pc_name']} | Usuario: {info['user']}")
            return info
        except Exception as e:
            self.log(f"Error cargando motor C++: {e}", level="error")
            return {"pc_name": "Unknown", "user": "Guest"}

    def speak(self, text):
        """El método que le da voz a Ruth"""
        # Loggeamos lo que dice para tener registro de la conversación
        self.log(f"BAYMAX DICE: {text}") 
        if self.speaker:
            try:
                self.speaker.Speak(text)
            except Exception as e:
                self.log(f"Error al hablar: {e}", level="error")

    def introduce_self(self):
        intro_text = f"¡Hola Inge! Soy {self.name}, tu asistente de inteligencia artificial. Estoy aquí para ayudarte a automatizar tareas y hacer tu vida más fácil. ¿En qué puedo asistirte hoy?"
        self.speak(intro_text)

    def execute_app(self, app_name, args=""):
        self.log(f"ACCIÓN: Ejecutando aplicación {app_name} {args}")
        self.speak(f"Abriendo {app_name}")
        
        if "notepad" in app_name.lower():
            target = "cmd.exe"
            arguments = "/c start notepad"
        else:
            target = app_name
            arguments = args
            
        success = ruth_backend.run_process(target, arguments)
        if not success:
            self.log(f"Fallo al ejecutar {app_name}", level="error")
        return success

    def kill_app(self, app_name):
        self.log(f"ACCIÓN: Intentando matar proceso {app_name}")
        self.speak(f"Deteniendo el proceso {app_name}")
        
        if not app_name.endswith(".exe"):
            app_name += ".exe"
            
        count = ruth_backend.kill_process_by_name(app_name)
        
        if count > 0:
            msg = f"He eliminado {count} instancias de {app_name}."
            self.speak(msg)
            self.log(f"Éxito: {msg}") # Confirmación en log
            return True
        else:
            self.speak(f"No encontré ningún proceso llamado {app_name}.")
            self.log(f"Fallo: Proceso {app_name} no encontrado", level="warning")
            return False
        
    def check_vitals(self):
        self.log("ACCIÓN: Iniciando chequeo de signos vitales")
        self.speak("Analizando signos vitales del sistema...")
        
        ram = ruth_backend.get_memory_status()
        disk = ruth_backend.get_disk_status()
        
        # Loggeamos los datos duros para análisis posterior
        self.log(f"VITALS - RAM: {ram['percent_used']}% | DISK FREE: {disk['free_gb']} GB")

        self.speak(f"Uso de memoria RAM al {ram['percent_used']} por ciento.")
        
        if ram['percent_used'] > 85:
            self.speak("⚠️ Inge: La memoria está saturada. Recomiendo cerrar aplicaciones.")
            self.log("ALERTA: Memoria saturada (>85%)", level="warning")
        
        free_gb = round(disk['free_gb'], 2)
        self.speak(f"Espacio libre en disco C: {free_gb} Gigabytes.")
        
        if disk['free_gb'] < 10.0:
            self.speak("⚠️ Crítico Inge: Queda muy poco espacio en disco.")
            self.log("ALERTA CRÍTICA: Disco casi lleno (<10GB)", level="error")
        else:
            self.speak("Inge Almacenamiento en niveles óptimos.")

    def inspect_downloads(self):
        self.log("ACCIÓN: Inspeccionando carpeta de Descargas")
        self.speak("Inspeccionando carpeta de Descargas...")
        
        downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
        files = ruth_backend.scan_directory(downloads_path)
        
        count = len(files)
        self.log(f"Archivos encontrados en Downloads: {count}")
        
        self.speak(f"He encontrado {count} archivos en tu carpeta de descargas.")
        
        if count > 20:
            self.speak("Tienes demasiados archivos acumulados Inge. Deberíamos hacer limpieza pronto.")
        else:
            self.speak("Tu carpeta está bastante ordenada. ¡Bien hecho!")

    def create_log_entry(self):
        self.log("ACCIÓN: Generando reporte escrito en Notepad")
        self.speak("Generando reporte de mantenimiento...")
        
        self.execute_app("notepad")
        
        import time
        time.sleep(3) 
        
        header = f"REPORTE RUTH - USUARIO: {self.system_info['user']}"
        ruth_backend.type_text(header)
        ruth_backend.press_enter()
        ruth_backend.press_enter() 
        
        ruth_backend.type_text(" Estado del sistema: ")
        ruth_backend.press_enter()
        
        ram = ruth_backend.get_memory_status()
        disk = ruth_backend.get_disk_status()
        
        ruth_backend.type_text(f"- RAM Usada: {ram['percent_used']}%")
        ruth_backend.press_enter()
        ruth_backend.type_text(f"- Disco Libre: {round(disk['free_gb'], 2)} GB")
        ruth_backend.press_enter()
        
        ruth_backend.press_enter()
        ruth_backend.type_text(" Fin del reporte. Atte: Ruth. ")
        
        self.speak("Reporte generado en pantalla.")
        self.log("Éxito: Reporte escrito finalizado")

    def demo_window_control(self):
        self.log("ACCIÓN: Iniciando demo de control visual")
        self.speak("Iniciando demostración de control de ventanas.")
        
        self.execute_app("notepad")
        import time
        time.sleep(2) 
        
        self.speak("Maximizando ventana.")
        target = "Bloc de notas" 
        
        if ruth_backend.maximize_window(target):
            time.sleep(3)
            ruth_backend.type_text(" Ruth tiene el control visual total de tu escritorio. ")
            time.sleep(4)
            
            self.speak("Cerrando ventana.")
            self.log("Cerrando ventana de demostración")
            ruth_backend.close_window_by_title(target)
        else:
            self.speak("No encontré la ventana del Bloc de notas.")
            self.log("Fallo: Ventana objetivo no encontrada", level="warning")

    def activate_presentation_mode(self):
        """Mueve el mouse sutilmente para evitar bloqueo de pantalla"""
        self.log("ACCIÓN: Activando Modo Presentación (Mouse Jiggler)")
        self.speak("Modo presentación activo. Moveré el mouse para mantener la sesión abierta.")
        
        # Obtenemos posición actual para no perder el mouse
        import time
        
        # Haremos esto 5 veces como demostración (en un caso real sería un bucle infinito hasta cancelar)
        for i in range(5):
            # Obtenemos dónde está el mouse
            pos = ruth_backend.get_mouse_position()
            x, y = pos[0], pos[1]
            
            # Lo movemos un poquito a la derecha
            ruth_backend.move_mouse(x + 20, y)
            time.sleep(0.5)
            
            # Lo regresamos
            ruth_backend.move_mouse(x, y)
            time.sleep(2) # Esperamos 2 segundos
            
        self.speak("Modo presentación finalizado.")
        self.log("Modo presentación desactivado")

    def start_autoclicker(self, clicks=50, interval=0.1):
        """Realiza clics automáticos con freno de emergencia"""
        self.log(f"ACCIÓN: Iniciando AutoClicker ({clicks} clics)")
        self.speak(f"Iniciando secuencia de {clicks} clics. Mantén presionado ESCAPE para cancelar.")
        
        # Damos 3 segundos para que el usuario coloque el mouse donde quiera
        import time
        time.sleep(3)
        
        count = 0
        try:
            for i in range(clicks):
                # 1. VERIFICACIÓN DE SEGURIDAD (Kill Switch)
                # 0x1B es el código hexadecimal para la tecla ESC
                if ruth_backend.is_key_pressed(0x1B): 
                    self.speak("Cancelación de emergencia detectada.")
                    self.log("AutoClicker abortado por usuario (ESC)")
                    break
                
                # 2. Acción
                ruth_backend.mouse_click(False) # False = Clic Izquierdo
                count += 1
                
                # 3. Espera entre clics (velocidad)
                time.sleep(interval)
                
        except Exception as e:
            self.log(f"Error en AutoClicker: {e}", level="error")
            
        self.speak(f"Secuencia finalizada. Realicé {count} clics.")

        def take_screenshot(self):
        #Toma una captura de pantalla y la guarda como evidencia"""
            self.log("ACCIÓN: Iniciando captura de pantalla")
            self.speak("Tomando captura de evidencia.")
        
        # 1. Crear directorio si no existe
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        shot_dir = os.path.join(base_dir, "screenshots")
        
        if not os.path.exists(shot_dir):
            os.makedirs(shot_dir)
            
        # 2. Generar nombre único: evidencia_2025-11-28_23-30-01.png
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"evidencia_{timestamp}.png"
        filepath = os.path.join(shot_dir, filename)
        
        try:
            # 3. Capturar y Guardar
            # PyAutoGUI hace la magia
            screenshot = pyautogui.screenshot()
            screenshot.save(filepath)
            
            self.speak("Captura guardada exitosamente.")
            self.log(f"Éxito: Screenshot guardado en {filename}")
            
            # Opcional: Abrir la imagen para que el usuario la vea (Confirmación visual)
            # Usamos nuestro propio motor C++ para abrirla, ¡porque podemos!
            ruth_backend.run_process(filepath, "")
            
        except Exception as e:
            self.speak("Hubo un error al guardar la imagen.")
            self.log(f"Error screenshot: {e}", level="error")

    def take_screenshot(self):
        """Toma una captura de pantalla y la guarda como evidencia"""
        self.log("ACCIÓN: Iniciando captura de pantalla")
        self.speak("Tomando captura de evidencia.")
        
        # 1. Crear directorio si no existe
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        shot_dir = os.path.join(base_dir, "screenshots")
        
        if not os.path.exists(shot_dir):
            os.makedirs(shot_dir)
            
        # 2. Generar nombre único: evidencia_2025-11-28_23-30-01.png
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"evidencia_{timestamp}.png"
        filepath = os.path.join(shot_dir, filename)
        
        try:
            # 3. Capturar y Guardar
            # PyAutoGUI hace la magia
            screenshot = pyautogui.screenshot()
            screenshot.save(filepath)
            
            self.speak("Captura guardada exitosamente.")
            self.log(f"Éxito: Screenshot guardado en {filename}")
            
            # Opcional: Abrir la imagen para que el usuario la vea (Confirmación visual)
            # Usamos nuestro propio motor C++ para abrirla, ¡porque podemos!
            ruth_backend.run_process(filepath, "")
            
        except Exception as e:
            self.speak("Hubo un error al guardar la imagen.")
            self.log(f"Error screenshot: {e}", level="error")

    def search_google(self, query):
        """Busca algo en Google usando el navegador predeterminado"""
        self.log(f"ACCIÓN: Buscando en Google: '{query}'")
        self.speak(f"Buscando {query} en Google.")
        
        query_encoded = urllib.parse.quote_plus(query)
        url = f"https://www.google.com/search?q={query_encoded}"
        
        # CORRECCIÓN: Pasamos la URL directa como "programa". 
        # Windows sabrá que hacer con ella.
        ruth_backend.run_process(url, "")

    def search_youtube(self, query):
        """Busca videos en YouTube"""
        self.log(f"ACCIÓN: Buscando en YouTube: '{query}'")
        self.speak(f"Buscando videos de {query}.")
        
        query_encoded = urllib.parse.quote_plus(query)
        url = f"https://www.youtube.com/results?search_query={query_encoded}"
        
        # CORRECCIÓN: Igual aquí, URL directa.
        ruth_backend.run_process(url, "")

    def clean_temp_files(self):
        """Elimina archivos de la carpeta temporal de Windows"""
        self.log("ACCIÓN: Iniciando limpieza de archivos temporales")
        self.speak("Iniciando protocolo de limpieza de archivos temporales.")
        
        # Ruta de temporales: C:\Users\TuUsuario\AppData\Local\Temp
        temp_path = os.environ.get('TEMP')
        
        if not temp_path:
            self.speak("No pude localizar la carpeta temporal.")
            return

        self.speak("Escaneando basura del sistema...")
        # Reusamos nuestro escáner C++
        files = ruth_backend.scan_directory(temp_path)
        
        total_files = len(files)
        deleted_count = 0
        
        # Intentamos borrar uno por uno
        for file in files:
            full_path = os.path.join(temp_path, file)
            
            # Llamamos al músculo destructor
            if ruth_backend.delete_file(full_path):
                deleted_count += 1
                
        self.log(f"Limpieza: {deleted_count} borrados de {total_files} encontrados.")
        
        if deleted_count > 0:
            self.speak(f"Limpieza finalizada. Eliminé {deleted_count} archivos basura.")
        else:
            self.speak("El sistema ya estaba limpio o los archivos están en uso.")

            # ... (métodos anteriores) ...

    def audit_session(self):
        """Reporta tiempo de actividad y sugiere reinicio si es necesario"""
        self.log("ACCIÓN: Auditando tiempo de sesión (Uptime)")
        
        # Obtenemos milisegundos y convertimos a horas
        ms = ruth_backend.get_system_uptime_ms()
        seconds = ms / 1000
        minutes = seconds / 60
        hours = minutes / 60
        
        # Formato bonito: "4 horas y 23 minutos"
        h_entero = int(hours)
        m_entero = int(minutes % 60)
        
        msg = f"Sistema activo por {h_entero} horas y {m_entero} minutos."
        self.speak(msg)
        self.log(f"UPTIME: {msg}")
        
        # Regla de T-Systems: Si lleva más de 3 días (72 horas) encendida, alerta.
        if hours > 72:
            self.speak("⚠️ Inge, el sistema lleva demasiado tiempo sin reiniciar. El rendimiento podría degradarse. Recomiendo un reinicio pronto.")
        elif hours < 1:
            self.speak("El sistema está fresco. Acabamos de arrancar.")
        else:
            self.speak("Tiempo de sesión dentro de parámetros normales.")

    def secure_station(self):
        """Bloquea la PC por seguridad"""
        self.log("ACCIÓN: Bloqueo de seguridad solicitado")
        self.speak("Bloqueando estación de trabajo. Hasta luego.")
        
        # Damos un segundo para que termine de hablar
        import time
        time.sleep(1)
        
        if not ruth_backend.lock_session():
            self.speak("Error. No pude bloquear la sesión.")

    def run_network_diagnostics(self):
        """Ejecuta un diagnóstico completo de red"""
        self.log("ACCIÓN: Iniciando diagnóstico de red")
        self.speak("Iniciando diagnóstico de red. Esto puede tardar unos segundos.")
        
        # 1. Chequeo Rápido (C++)
        if ruth_backend.check_internet_connection():
            self.speak("Conectividad básica: ESTABLE. Tenemos salida a internet.")
            self.log("Internet: OK")
        else:
            self.speak("⚠️ Alerta: No detecto conexión a internet. Verifica tu cable o Wi-Fi.")
            self.log("Internet: CAÍDO", level="error")
            return # Si no hay internet, no podemos hacer speedtest

        # 2. Prueba de Velocidad (Python)
        self.speak("Midiendo velocidad de la red. Por favor espera...")
        
        try:
            st = speedtest.Speedtest()
            st.get_best_server() # Busca el servidor más cercano
            
            # Descarga
            download_bps = st.download()
            download_mbps = round(download_bps / 1048576, 2) # Convertir bits a Megabits
            
            # Subida
            upload_bps = st.upload()
            upload_mbps = round(upload_bps / 1048576, 2)
            
            ping = int(st.results.ping)
            
            report = f"Velocidad de bajada: {download_mbps} Megas. Subida: {upload_mbps} Megas. Latencia: {ping} milisegundos."
            self.speak(report)
            self.log(f"SPEEDTEST: Down={download_mbps}Mbps, Up={upload_mbps}Mbps, Ping={ping}ms")
            
            if download_mbps < 10:
                self.speak("La red está inusualmente lenta, Inge.")
            else:
                self.speak("La velocidad de la red es óptima.")
                
        except Exception as e:
            self.speak("Hubo un error midiendo la velocidad.")
            self.log(f"Error Speedtest: {e}", level="error")

    def draft_email(self, recipient, subject, body):
        """Prepara un correo electrónico en el cliente predeterminado"""
        self.log(f"ACCIÓN: Redactando correo para {recipient}")
        self.speak(f"Abriendo cliente de correo para escribir a {recipient}.")
        
        # Codificamos los textos para que espacios y tildes no rompan el link
        recip_enc = urllib.parse.quote(recipient)
        sub_enc = urllib.parse.quote(subject)
        body_enc = urllib.parse.quote(body)
        
        # Construimos el "Hechizo" (URI Scheme)
        mailto_link = f"mailto:{recip_enc}?subject={sub_enc}&body={body_enc}"
        
        # Usamos el músculo C++ existente
        # Nota: Como es un protocolo, Windows sabe qué app abrir
        ruth_backend.run_process(mailto_link, "")

    def send_status_email(self):
        """Genera y prepara el correo de reporte automáticamente"""
        self.log("ACCIÓN: Preparando correo de reporte de estado")
        self.speak("Recopilando datos y preparando correo...")
        
        # 1. Obtenemos datos (Aquí SÍ podemos usar ruth_backend porque estamos en core.py)
        ram = ruth_backend.get_memory_status()
        disk = ruth_backend.get_disk_status()
        
        # 2. Definimos destinatario y asunto
        destinatario = "soporte@t-systems.com"
        asunto = f"Reporte de Estado - {self.system_info['pc_name']}"
        
        # 3. Construimos el cuerpo
        cuerpo = (
            f"Hola equipo,\n\n"
            f"Envío reporte de estado automático:\n"
            f"- RAM Usada: {ram['percent_used']}%\n"
            f"- Disco C Libre: {round(disk['free_gb'], 2)} GB\n\n"
            f"Saludos,\n{self.system_info['user']}"
        )
        
        # 4. Llamamos a la función de borrador que ya teníamos
        self.draft_email(destinatario, asunto, cuerpo)

    def set_volume(self, percent):
        """Ajusta el volumen del sistema"""
        self.log(f"ACCIÓN: Ajustando volumen al {percent}%")
        
        # Validación de seguridad
        if percent > 100: percent = 100
        if percent < 0: percent = 0
        
        # Conversión matemática
        scalar = percent / 100.0
        
        if ruth_backend.set_master_volume(scalar):
            self.speak(f"Volumen ajustado al {percent} por ciento.")
        else:
            self.speak("No pude acceder al controlador de audio.")

    def mute_system(self):
        self.log("ACCIÓN: Silenciando sistema")
        ruth_backend.set_mute(True) # True = Mute ON
        # No hablamos aquí porque... bueno, acabamos de silenciarla xD
        # Pero podemos imprimir en consola
        print("🔇 SISTEMA SILENCIADO")

    def unmute_system(self):
        self.log("ACCIÓN: Reactivando sonido")
        ruth_backend.set_mute(False) # False = Mute OFF
        self.speak("Audio restaurado.")

    def tell_time_date(self):
        """Dice la hora y fecha actual"""
        now = datetime.now()
        
        # Formato de hora: "Son las 3 y 45"
        hora = now.hour
        minutos = now.minute
        
        # Pequeña lógica para que suene natural
        if minutos == 0:
            time_str = f"Son las {hora} en punto."
        elif minutos == 30:
            time_str = f"Son las {hora} y media."
        else:
            time_str = f"Son las {hora} con {minutos} minutos."
            
        # Formato de fecha: "Hoy es viernes 28 de noviembre"
        # Mapeo rápido de días y meses (Python suele darlos en inglés si no configuramos locale)
        dias = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
        meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
        
        dia_sem = dias[now.weekday()]
        mes = meses[now.month - 1]
        
        date_str = f"Hoy es {dia_sem} {now.day} de {mes}."
        
        full_msg = f"{time_str} {date_str}"
        self.speak(full_msg)
        self.log(f"INFO TIEMPO: {full_msg}")

    def _start_browser_engine(self):
        if self.browser:
            return True

        self.log("ACCIÓN: Iniciando motor Selenium (Google Chrome)")
        self.speak("Transfiriendo conciencia al navegador Chrome...")
        
        try:
            # 1. Configuración de Chrome (MODIFICADA PARA SIGILO)
            chrome_options = ChromeOptions()
            chrome_options.add_argument("--start-maximized")
            
            # Ocultar el cartel "Chrome is being controlled by automated test software"
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # El camuflaje principal: Desactivar la bandera de robot
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            
            # (Opcional) Cambiar el User-Agent para parecer un navegador humano común
            chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            # 2. Descarga e instalación automática del Driver de Chrome
            # Usamos ChromeDriverManager para que siempre coincida con tu versión
            service = ChromeService(ChromeDriverManager().install())
            
            # 3. Encendido del motor
            self.browser = webdriver.Chrome(service=service, options=chrome_options)
            
            self.log("Éxito: Motor Chrome online y sincronizado")
            return True
            
        except Exception as e:
            self.speak("Falla crítica en la matriz de Chrome.")
            self.log(f"Error Selenium Chrome: {e}", level="error")
            return False

    def close_browser(self):
        """Cierra el navegador controlado"""
        if hasattr(self, 'browser') and self.browser:
            self.log("ACCIÓN: Cerrando navegador automatizado")
            self.speak("Cerrando sesión web.")
            self.browser.quit()
            self.browser = None
        else:
            self.speak("No hay ningún navegador activo.")

    def automate_instagram_login(self):
        """Prueba de concepto: Login en Instagram"""
        # 1. Cargar credenciales
        username = os.getenv("INSTAGRAM_USER")
        password = os.getenv("INSTAGRAM_PASS")
        
        if not username or not password:
            self.speak("Error. Faltan las credenciales en el archivo punto env.")
            return

        # 2. Iniciar navegador
        if not self._start_browser_engine():
            return

        self.speak("Navegando a Instagram...")
        self.log("ACCIÓN: Iniciando secuencia de Login en Instagram")
        
        try:
            self.browser.get("https://www.instagram.com")
            
            self.speak("Localizando campos de acceso con espera inteligente...")
            
            # --- LA MAGIA T-SYSTEMS: ESPERA EXPLÍCITA ---
            # Creamos un "vigilante" que esperará un MÁXIMO de 20 segundos
            wait = WebDriverWait(self.browser, 20)
            
            
            # En lugar de visibility (que falla por las capas superpuestas de CSS),
            # usamos presence_of_element_located: "Si existe en el HTML, agárralo".
            # Y usamos XPATH apuntando directamente a la etiqueta <input>
            
            user_box = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@name='username']")))
            pass_box = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@name='password']")))
            
            # 4. INYECTAR DATOS
            self.speak("Campos localizados en el DOM. Inyectando credenciales...")
            
            # Truco Ninja: Como a veces Instagram bloquea el .clear() estándar, 
            # mandamos directamente las teclas
            user_box.send_keys(username)
            time.sleep(0.5) 
            
            pass_box.send_keys(password)
            time.sleep(0.5)
            
            # 5. DAR ENTER
            self.speak("Iniciando sesión.")
            pass_box.send_keys(Keys.ENTER)
            
            # 6. ESPERAR RESULTADO
            time.sleep(6) # Esperamos a que cargue el Feed
            
            # Verificación simple: Si la URL cambió, entramos
            if "login" not in self.browser.current_url:
                self.speak("¡Acceso concedido! Estamos dentro, Inge.")
                self.log("Éxito: Login completado")
            else:
                self.speak("Parece que seguimos en la página de login. Verifica tus datos.")
            
        except Exception as e:
            # --- DIAGNÓSTICO FORENSE ---
            self.speak("La infiltración falló. Tomando evidencia visual del obstáculo.")
            
            # Guardamos una captura de pantalla en la carpeta del proyecto
            screenshot_path = os.path.join(os.getcwd(), "error_login_instagram.png")
            try:
                self.browser.save_screenshot(screenshot_path)
                self.log(f"Evidencia visual guardada en: {screenshot_path}")
            except Exception as snap_error:
                self.log(f"No se pudo tomar la foto: {snap_error}")

            self.log(f"Error Login: {e}", level="error")

    def interact_feed(self, actions=3):
        """
        Navega por el feed, scrollea y da likes aleatorios.
        Versión Depurada: Busca elementos de forma agresiva.
        """
        if not self.browser:
            self.speak("El navegador no está activo. Inícialo primero.")
            return

        self.log("ACCIÓN: Iniciando interacción social en Instagram")
        self.speak(f"Navegando el feed. Realizaré {actions} interacciones.")
        
        try:
            for i in range(actions):
                # 1. SCROLL
                scroll_amount = random.randint(500, 800)
                self.browser.execute_script(f"window.scrollBy(0, {scroll_amount});")
                sleep_time = random.uniform(2.0, 4.0)
                time.sleep(sleep_time)
                
                # 2. BÚSQUEDA AGRESIVA (Wildcard)
                # Buscamos CUALQUIER elemento (*) que tenga el texto "Like" o "Me gusta"
                # Esto cubre svg, button, div, span, etc.
                try:
                    # XPath Maestro: Busca 'Like' (Inglés), 'Me gusta' (Español)
                    # Y nos aseguramos que NO sea "Unlike" (Ya dado like) o "Ya no me gusta"
                    xpath = "//*[@aria-label='Like' or @aria-label='Me gusta']"
                    
                    possible_likes = self.browser.find_elements(By.XPATH, xpath)
                    
                    # --- BLOQUE DE DIAGNÓSTICO ---
                    # Esto nos dirá en la consola qué encontró
                    if possible_likes:
                        print(f"👀 Detecté {len(possible_likes)} elementos 'Like' en esta pantalla.")
                    else:
                        print("👀 No veo botones de Like. Intentando buscar por clase...")
                    # -----------------------------

                    if possible_likes:
                        # Elegimos uno visible
                        target = None
                        for btn in possible_likes:
                            if btn.is_displayed():
                                target = btn
                                break
                        
                        if target and random.random() < 0.7:
                            # ESTRATEGIA NUEVA: Subir al padre
                            try:
                                # Intentamos clic directo con JS primero
                                self.browser.execute_script("arguments[0].click();", target)
                            except:
                                # Si falla, buscamos al padre (el botón real) y le damos clic a él
                                parent = target.find_element(By.XPATH, "./..")
                                self.browser.execute_script("arguments[0].click();", parent)
                            
                            self.speak("Di un like.")
                            self.log("Interacción: LIKE exitoso")
                            time.sleep(3)
                        else:
                            self.log("Decisión: Salté este post.")
                    else:
                        self.log("Info: No encontré corazones vacíos en este tramo.")

                except Exception as e_like:
                    self.log(f"Fallo al intentar dar like: {e_like}", level="warning")
                    
        except Exception as e:
            self.speak("Tuve problemas para navegar el feed.")
            self.log(f"Error Feed: {e}", level="error")
            
        self.speak("Ciclo de interacción finalizado.")