# -*- coding: utf-8 -*-
import ollama
from ruth.settings import Config # Invocamos la matriz

class RuthBrain:
    def __init__(self):
        # 1. Instanciamos la configuración
        config = Config()
        # 2. Extraemos los valores de la matriz (con valores de respaldo por si falla)
        self.model = config.get("ai.text_model", "llama3.2")
        # EL PERSONAJE (System Prompt)
        # Definimos qui�n es ella antes de que empiece la pel�cula
        # 2. Extraemos los valores de la matriz (con valores de respaldo por si falla)
        self.model = config.get("ai.text_model", "llama3.2")
        self.system_prompt = config.get("ai.system_prompt", "Eres Baymax, un asistente de IA...")
        
        self.chat_history = [
            {'role': 'system', 'content': self.system_prompt}
        ]

    def think(self, user_input):
        """Procesa el pensamiento con STREAMING (Flujo continuo)"""
        try:
            self.chat_history.append({'role': 'user', 'content': user_input})
            
            # Activamos stream=True
            stream = ollama.chat(
                model=self.model, 
                messages=self.chat_history,
                stream=True, # <--- LA CLAVE DE LA VELOCIDAD PERCIBIDA
            )
            
            full_response = ""
            print("🧠 RUTH PENSANDO: ", end="", flush=True)
            
            # Bucle de Streaming: Imprimimos cada palabra apenas nace
            for chunk in stream:
                part = chunk['message']['content']
                print(part, end="", flush=True) # Efecto máquina de escribir
                full_response += part
                
            print("\n") # Salto de línea al terminar
            
            # Guardamos la respuesta completa en la memoria
            self.chat_history.append({'role': 'assistant', 'content': full_response})
            
            # Gestión de memoria (Mantenemos últimos 10 mensajes)
            if len(self.chat_history) > 20: 
                self.chat_history = [self.chat_history[0]] + self.chat_history[-10:]
            
            return full_response
            
        except Exception as e:
            return f"Error cognitivo: {e}"
    def clear_memory(self):
        """Reinicia la conversacion"""
        self.chat_history = [self.system_message]