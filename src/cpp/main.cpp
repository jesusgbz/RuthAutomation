#include <pybind11/pybind11.h>

namespace py = pybind11;

// Una función simple de C++ que suma dos números
int sumar_numeros(int i, int j) {
    return i + j;
}

// Aquí es donde definimos cómo Python verá este código
PYBIND11_MODULE(ruth_backend, m) {
    m.doc() = "Módulo central de C++ para Ruth"; // Documentación del módulo

    // Exponemos la función 'sumar_numeros' a Python llamándola 'sumar'
    m.def("sumar", &sumar_numeros, "Una función que suma dos números");
}