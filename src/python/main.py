from ruth.core import RuthAssistant
import time

def main():
    app = RuthAssistant()
    
    # Saludo personalizado (¡Déjalo como Buzz Lightyear si quieres!)
    app.introduce_self()
    
    # Inspección de archivos
    app.inspect_downloads()
    
    app.speak("Reporte de archivos finalizado.")

if __name__ == "__main__":
    main()