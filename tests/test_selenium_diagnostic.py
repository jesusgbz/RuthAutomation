import os
from selenium import webdriver
from selenium.webdriver.edge.service import Service

# RUTA DIRECTA AL DRIVER QUE PEGASTE
# Asumimos que está en la misma carpeta que este script o en src/python
base_dir = os.path.dirname(os.path.abspath(__file__))
driver_path = os.path.join(base_dir, "msedgedriver.exe")

print(f"--- DIAGNÓSTICO MANUAL ---")
print(f"Buscando driver en: {driver_path}")

if not os.path.exists(driver_path):
    print("❌ ERROR: No encuentro msedgedriver.exe en esa ruta.")
    print("Por favor descarga el driver y pégalo junto a este script.")
    exit()

try:
    print("1. Iniciando Servicio Manual...")
    # Le decimos explícitamente dónde está el exe
    service = Service(executable_path=driver_path)
    
    print("2. Configurando Opciones...")
    options = webdriver.EdgeOptions()
    options.add_argument("--start-maximized")
    
    # --- PRUEBA CRUCIAL: SIN ARGUMENTOS RAROS ---
    # A veces menos es más. Probemos una conexión limpia.
    
    print("3. Lanzando Navegador...")
    driver = webdriver.Edge(service=service, options=options)
    
    print("4. Navegando a Google...")
    driver.get("https://www.google.com")
    print("✅ ¡ÉXITO TOTAL! El sistema funciona.")
    
    input("Presiona Enter para cerrar...")
    driver.quit()

except Exception as e:
    print(f"\n❌ FALLO: {e}")