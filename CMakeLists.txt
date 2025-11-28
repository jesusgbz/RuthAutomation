cmake_minimum_required(VERSION 3.20)

project(RuthAutomation VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# --- CORRECCIÓN ---

# 1. LA ORDEN DIRECTA:
# Le decimos a CMake: "Antes de buscar en Windows, mira en la carpeta 'venv' que está aquí mismo".
# ${CMAKE_CURRENT_SOURCE_DIR} es la ruta donde está este archivo.
set(Python3_ROOT_DIR "${CMAKE_CURRENT_SOURCE_DIR}/venv")

# 2. ENCONTRAR AL PILOTO (PYTHON) PRIMERO:
# Buscamos Python ANTES de llamar a pybind11.
# Esto asegura que pybind11 use lo que nosotros encontramos, no lo que él quiera.
find_package(Python3 COMPONENTS Interpreter Development REQUIRED)

# 3. AHORA SÍ, EL TRADUCTOR:
add_subdirectory(extern/pybind11)

# ------------------

# 4. Creamos el módulo
pybind11_add_module(ruth_backend src/cpp/main.cpp)

# Mensajes de confirmación (Para que duermas tranquilo)
message(STATUS "---------------------------------------------------")
message(STATUS "RUTH CONFIG: Usando Python en: ${Python3_EXECUTABLE}")
message(STATUS "RUTH CONFIG: Versión detectada: ${Python3_VERSION}")
message(STATUS "---------------------------------------------------")