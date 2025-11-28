import sys
import os

# Verificación de seguridad: Imprimimos dónde estamos y qué Python usamos
print(f"--- Iniciando Sistema Ruth ---")
print(f"Python Ejecutando: {sys.executable}")

try:
    # INTENTO DE IMPORTAR EL MÓDULO C++
    # Python buscará un archivo .pyd en la misma carpeta llamado 'ruth_backend'
    import ruth_backend
    print("✅ Módulo C++ 'ruth_backend' importado correctamente.")
except ImportError as e:
    print(f"❌ Error fatal: No encuentro el músculo de C++. {e}")
    sys.exit(1)

# PROBANDO LA FUNCIÓN
# Aquí Python llama a la función escrita en C++
try:
    num1 = 10
    num2 = 25
    resultado = ruth_backend.sumar(num1, num2)
    
    print(f"\n🧪 PRUEBA DE INTEROPERABILIDAD:")
    print(f"   Python dice: 'C++, suma {num1} + {num2}'")
    print(f"   C++ responde: {resultado}")
    
    if resultado == 35:
        print("\n🚀 ¡ÉXITO! La conexión Neurona-Músculo funciona.")
    else:
        print("\n⚠️ ALERTA: El cálculo es incorrecto.")

except Exception as e:
    print(f"Error al ejecutar función: {e}")