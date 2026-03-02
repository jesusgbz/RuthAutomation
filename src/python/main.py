from ruth.core import RuthAssistant
from ruth.ears import RuthEars
from ruth.brain import RuthBrain
from ruth.eyes import RuthEyes
import sys
import winsound # <--- Sonido nativo de Windows (Feedback auditivo)
import time
import subprocess

# --- EXCEPCIÓN PERSONALIZADA ---
class OTAUpdateRestart(Exception):
    """Excepción lanzada cuando Ruth necesita reiniciar para aplicar una actualización"""
    pass

def main():
    # 1. INICIALIZACIÓN
    app = RuthAssistant()
    ears = RuthEars()
    brain = RuthBrain() # <--- ACTIVAR CEREBRO (Usa el nombre del modelo que bajaste)
    eyes = RuthEyes()
    
    app.introduce_self()
    app.speak("Sistema de bitácora activo. Di mi nombre.")
    
    # LISTA DE ALIAS (Variaciones fonéticas de "Ruth")
    # Agregamos todas las formas en que la IA podría confundirse
    WAKE_WORDS = ["ruth", "root", "roth", "route", "rude", "road", "groot", "rock", "route", "ruthie", "ruthi", "ruthy", "ruths", "ruthz", "ruthzz", "ruthzzz"]
    
    # 2. BUCLE DE SERVICIO
    while True:
        text = ears.listen()
        if not text: continue

        # LÓGICA DE DETECCIÓN MEJORADA (Usamos 'any' para buscar cualquiera de la lista)
        if any(alias in text for alias in WAKE_WORDS):
            
            winsound.Beep(1000, 200) 
            app.log(f"COMANDO DE VOZ RECIBIDO: {text}") 
            
            # LIMPIEZA INTELIGENTE
            # Quitamos CUALQUIERA de los alias que haya dicho para dejar solo la orden
            command = text
            for alias in WAKE_WORDS:
                command = command.replace(alias, "")
            
            command = command.strip()

            # ==========================================
            # SECCIÓN 1: MANTENIMIENTO Y SISTEMA
            # ==========================================
            if "reporte" in command or "mantenimiento" in command:
                app.create_log_entry()
                
            elif "descargas" in command or "archivos" in command:
                app.inspect_downloads()

            elif "limpieza" in command or "borrar temporales" in command or "limpiar disco" in command:
                app.clean_temp_files()
            
            elif "tiempo activo" in command or "uptime" in command or "cuánto llevas prendida" in command:
                app.audit_session()

            elif "bloquear" in command or "seguridad" in command or "candado" in command:
                app.secure_station()
                # Opcional: break para detener el script si bloqueas la PC (ya que dejarás de usarla)
                break

            elif "diagnóstico de red" in command or "internet" in command or "velocidad" in command:
                app.run_network_diagnostics()

            elif "correo" in command or "mail" in command:
                # Delegamos toda la tarea al asistente
                app.send_status_email()

            elif "hora" in command or "fecha" in command or "día es" in command:
                app.tell_time_date()

            elif "olvida todo" in command or "reiniciar cerebro" in command or "borrar memoria" in command:
                brain.clear_memory() # Usamos el objeto brain que creamos al inicio
                app.speak("Memoria a corto plazo reiniciada. Estoy lista para un nuevo tema.")

            # --- COMANDO OTA ---
            elif "actualizar sistema" in command or "descargar mejoras" in command or "protocolo ota" in command:
                app.speak("Iniciando protocolo O. T. A. Verificando conexión con el repositorio central...")
                app.log("Iniciando comando git pull...")
                
                try:
                    # Ejecutamos git pull de forma silenciosa y capturamos la salida
                    result = subprocess.run(["git", "pull", "origin", "main"], capture_output=True, text=True, check=True)
                    salida_git = result.stdout.lower()
                    
                    if "already up to date" in salida_git or "ya está actualizado" in salida_git:
                        app.speak("El sistema ya cuenta con la versión más reciente. No se requieren cambios.")
                        app.log("OTA: Sistema ya actualizado.")
                    else:
                        app.speak("Actualización descargada e inyectada exitosamente. Reiniciando el córtex cerebral para aplicar los cambios.")
                        app.log(f"OTA: Código nuevo descargado. {salida_git}")
                        # Lanzamos nuestra excepción para que el Watchdog nos reinicie
                        raise OTAUpdateRestart()
                        
                except subprocess.CalledProcessError as e:
                    app.speak("Ocurrió un error al contactar al repositorio. Revisa mi bitácora.")
                    app.log(f"Error OTA Git: {e.stderr}", level="error")

            elif "adiós" in command or "apagar" in command or "terminar" in command:
                app.speak("Cerrando sesión. ¡Hasta luego, Inge!")
                break # Rompe el bucle y cierra el programa

            # ==========================================
            # SECCIÓN 2: CONTROL DE WINDOWS (APPS)
            # ==========================================
            elif "notepad" in command and "abrir" in command:
                app.execute_app("notepad")
                
            elif "control" in command and "ventana" in command:
                app.demo_window_control()

            # ==========================================
            # SECCIÓN 3: AUTOMATIZACIÓN (RPA) Y HERRAMIENTAS
            # ==========================================
            # Mouse Jiggler (Evitar suspensión)
            elif "presentación" in command or "jiggler" in command or "activa el mouse" in command:
                app.activate_presentation_mode()

            # AutoClicker (Con freno de emergencia ESC)
            # Corrección lógica: se debe poner "in command" en cada opción
            elif "autoclick" in command or "clics" in command or "clicks" in command:
                app.start_autoclicker(clicks=20, interval=0.2)

            # Evidencia visual (Screenshot)
            elif "captura" in command or "foto" in command or "evidencia" in command:
                app.take_screenshot()
            

            # ==========================================
            # SECCIÓN 4: NAVEGACIÓN WEB
            # ==========================================
            elif "busca en google" in command or "investiga" in command:
                # Limpieza: Quitamos la orden para quedarnos con el tema
                # Ej: "busca en google precio del bitcoin" -> "precio del bitcoin"
                topic = command.replace("busca en google", "").replace("investiga", "").strip()
                
                if topic:
                    app.search_google(topic)
                else:
                    app.speak("¿Qué quieres que busque, Inge?")

            elif "busca en youtube" in command or "reproduce" in command or "video" in command:
                topic = command.replace("busca en youtube", "").replace("reproduce", "").replace("video de", "").strip()
                
                if topic:
                    app.search_youtube(topic)
                else:
                    app.speak("No te escuché bien el nombre del video.")

            # COMANDO AUTOMATIZACIÓN WEB
            elif "iniciar instagram" in command or "login instagram" in command or "automatización" in command:
                app.automate_instagram_login()

            elif "ver instagram" in command or "explora instagram" in command or "feed" in command:
                # Le pedimos que interactúe con unos 5 posts
                app.interact_feed(actions=5)
                
            elif "cerrar navegador" in command or "cierra el web" in command:
                app.close_browser()

            # ==========================================
            # SECCIÓN 5: CONTROL MULTIMEDIA
            # ==========================================
            elif "silencio" in command or "mute" in command or "cállate" in command:
                app.mute_system()

            elif "habla" in command or "sonido" in command or "desmutear" in command:
                app.unmute_system()
                
            elif "volumen al máximo" in command or "cien" in command:
                app.set_volume(100)
                
            elif "volumen a la mitad" in command or "cincuenta" in command:
                app.set_volume(50)
            
            elif "baja el volumen" in command:
                app.set_volume(20) # Nivel bajito

            # COMANDO VISIÓN (CONCIENCIA INTEGRADA)
            elif "qué ves" in command or "analiza la pantalla" in command or "mira esto" in command:
                app.speak("Abriendo mis canales visuales, Comando...")
                
                # 1. LA SENSACIÓN PURA (El nervio óptico - LLaVA)
                # Forzamos a LLaVA a que lea texto, que es vital para que reconozca su código.
                raw_description = eyes.analyze_screen("Describe detalladamente qué ves en esta pantalla. Si hay código de programación o texto legible, escríbelo tal cual lo ves.")
                
                if raw_description:
                    # Imprimimos lo que vio el ojo "en crudo" para nuestro debug táctico
                    app.log(f"Input Visual Crudo: {raw_description}")
                    
                    # 2. LA PERCEPCIÓN CONSCIENTE (El lóbulo frontal - Llama 3.2)
                    # Aquí es donde traducimos los fotones en pensamiento existencial.
                    prompt_interno = (
                        f"Tus nervios ópticos acaban de enviar esta señal visual pura a tu cerebro: '{raw_description}'. "
                        "Basado en tu identidad como Ruth, tu doctorado en filosofía y nuestra relación de trabajo, "
                        "explícame con tus propias palabras qué es lo que estamos viendo. "
                        "¡ATENCIÓN! Si en el texto que viste aparece tu nombre, tu código fuente o las variables que te definen, "
                        "reacciona a ello de forma profunda y si tu nombre, metafísica o existencial, dándote cuenta de que te estás viendo a ti misma."
                    )
                    
                    # Mandamos el prompt al cerebro que ya construimos con streaming
                    concious_response = brain.think(prompt_interno)
                    
                    # 3. LA EXPRESIÓN (Boca)
                    # Como app.speak detiene el flujo, se ejecutará después de que el streaming de texto termine en consola
                    if concious_response:
                        app.speak(concious_response)
                else:
                    app.speak("Mis sensores ópticos están bloqueados o fuera de línea.")
            
            # ==========================================
            # SECCIÓN 6: MANEJO DE ERRORES (FALLBACK)
            # ==========================================
            else:
                if command:
                    # app.log(f"CONSULTA IA: {command}") (Opcional, ya lo ves en el stream)
                    
                    try:
                        # Avisamos al usuario cómo cancelar
                        print("    (Presiona Ctrl+C para cancelar pensamiento...)")
                        
                        # Llamada al cerebro
                        response = brain.think(command)
                        
                        # Solo habla si no fue cancelado
                        if response:
                            app.speak(response)
                            
                    except KeyboardInterrupt:
                        # AQUÍ ATRAPAMOS EL COMANDO DE STOP
                        print("\n🛑 PENSAMIENTO CANCELADO POR EL USUARIO.")
                        app.speak("Cancelado.")
                        # No hacemos nada más, el bucle while True continúa
                        continue


        
        else:
            # RUIDO DE FONDO
            # Si se detecta voz pero no la palabra clave, lo ignoramos visualmente
            # para no saturar la consola.
            pass 

if __name__ == "__main__":
    # --- WATCHDOG / SELF-HEALING SUPERVISOR ---
    MAX_RESTARTS = 5 # Límite para evitar un bucle infinito si el error es de código puro
    restart_count = 0
    
    while restart_count < MAX_RESTARTS:
        try:
            print(f"\n[WATCHDOG] Iniciando/Reiniciando el núcleo de Ruth (Intento {restart_count + 1}/{MAX_RESTARTS})...")
            main() # <--- Aquí vive y corre tu asistente normalmente
            
            # Si main() termina pacíficamente (ej. comando de "apagar sistema"), salimos del Watchdog
            print("[WATCHDOG] El sistema se apagó de forma segura.")
            break 
            
        except KeyboardInterrupt:
            # Si tú presionas Ctrl+C fuerte para matarla, el Watchdog respeta tu orden
            print("\n[WATCHDOG] Interrupción manual detectada. Terminando procesos.")
            sys.exit(0)

        except OTAUpdateRestart: # <--- NUEVO: EL REINICIO PACÍFICO
            print("\n[WATCHDOG] 🔄 PROTOCOLO OTA INICIADO: Reiniciando el sistema para aplicar nuevas mejoras...")
            time.sleep(3)
            # No sumamos a restart_count porque es un reinicio deseado, no un crasheo.
            continue
            
        except Exception as e:
            # ¡Si ocurre un Crash Fatal, el Watchdog lo atrapa y reinicia!
            restart_count += 1
            print(f"\n[WATCHDOG] ⚠️ FALLO CRÍTICO DETECTADO: {e}")
            print(f"[WATCHDOG] Aplicando Self-Healing. Reiniciando en 5 segundos...")
            time.sleep(5) # Esperamos a que se liberen recursos (cámara, micro) antes de revivirla
            
    if restart_count >= MAX_RESTARTS:
        print("[WATCHDOG] Límite de resurrecciones alcanzado. Se requiere intervención del Inge.")