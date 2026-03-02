import os
import sys
import json
import pyaudio
from vosk import Model, KaldiRecognizer, SetLogLevel

class RuthEars:
    def __init__(self):
        # 1. SILENCIAMOS LOS LOGS DEL SISTEMA (Truco de optimización)
        SetLogLevel(-1)
        # Buscamos el modelo en la carpeta src/python/model
        # Truco para que funcione sin importar desde dónde ejecutes el script
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        model_path = os.path.join(base_path, "model")

        if not os.path.exists(model_path):
            print(f"❌ ERROR CRÍTICO: No encuentro el modelo en {model_path}")
            print("Descárgalo de https://alphacephei.com/vosk/models y ponlo en src/python/model")
            sys.exit(1)

        print(f"Loading AI Model form: {model_path}...")
        self.model = Model(model_path)
        self.recognizer = KaldiRecognizer(self.model, 16000)
        
        # Configuración del Micrófono
        self.mic = pyaudio.PyAudio()
        self.stream = self.mic.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8192)
        self.stream.start_stream()

    def listen(self):
        """Escucha el micrófono y devuelve texto solo cuando hay una frase completa"""
        print("👂 Escuchando...")
        
        while True:
            data = self.stream.read(4096, exception_on_overflow=False)
            
            if self.recognizer.AcceptWaveform(data):
                result = json.loads(self.recognizer.Result())
                text = result.get("text", "")
                
                if text:
                    print(f"🎤 Oído: '{text}'")
                    return text.lower() # Devolvemos todo en minúsculas para facilitar comparaciones

    def __del__(self):
        # Limpieza de recursos
        try:
            self.stream.stop_stream()
            self.stream.close()
            self.mic.terminate()
        except:
            pass