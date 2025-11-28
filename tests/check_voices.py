import pyttsx3

engine = pyttsx3.init()
voices = engine.getProperty('voices')

print("--- LISTA DE VOCES DETECTADAS ---")
for index, voice in enumerate(voices):
    print(f"ID: {voice.id}")
    print(f"Nombre: {voice.name}")
    print(f"Idiomas: {voice.languages}")
    print("---------------------------------")