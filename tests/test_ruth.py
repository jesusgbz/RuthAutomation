import sys
import time
import ruth_backend 

print(f"--- RUTH AUTOMATION v0.2 ---")

# 1. Verificamos identidad
info = ruth_backend.get_system_info()
print(f"🔧 Conectado a: {info['pc_name']} (Usuario: {info['user']})")

# 2. Pruebas de Automatización
print("\n--- INICIANDO PROTOCOLO DE APERTURA ---")

programs_to_open = [
    # TRUCO: "cmd /c start notepad" le dice a CMD: "Arranca, lanza notepad y ciérrate tú"
    ("cmd.exe", "/c start notepad"), 
    
    # Este estaba bien
    ("cmd.exe", "/k echo HOLA INGE"), 
    
    # Este también estaba bien
    ("msedge.exe", "www.google.com")  
]

for app, args in programs_to_open:
    print(f"⏳ Intentando lanzar: {app} {args}...")
    success = ruth_backend.run_process(app, args)
    
    if success:
        print(f"   ✅ ÉXITO: {app} ejecutado.")
    else:
        print(f"   ❌ ERROR: No se pudo lanzar {app}.")
    
    # Pausa dramática de 1 segundo entre acciones para que se vea "pro"
    time.sleep(2.5) 

print("\n🤖 Ciclo de pruebas finalizado.")