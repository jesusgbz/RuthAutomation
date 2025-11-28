#include <pybind11/pybind11.h>
#include <pybind11/stl.h> // <--- ¡ESTA ES LA CLAVE! Convierte std::vector a Python list
#include <windows.h>
#include <Lmcons.h>
#include <shellapi.h>
#include <tlhelp32.h> // <--- NUEVA LIBRERÍA: Para ver y matar procesos
#include <string>
#include <vector>
#include <iostream>
#include <filesystem> // <--- C++17 Standard Filesystem

namespace fs = std::filesystem; // Alias para escribir menos
namespace py = pybind11;

// --- UTILS ---
std::string get_computer_name() {
    char buffer[MAX_COMPUTERNAME_LENGTH + 1];
    DWORD size = sizeof(buffer);
    if (GetComputerNameA(buffer, &size)) return std::string(buffer);
    return "DESCONOCIDO";
}

std::string get_user_name() {
    char buffer[UNLEN + 1];
    DWORD size = sizeof(buffer);
    if (GetUserNameA(buffer, &size)) return std::string(buffer);
    return "DESCONOCIDO";
}

// --- FUNCIONES DE EJECUCIÓN ---
bool run_process(std::string program, std::string arguments) {
    HINSTANCE result = ShellExecuteA(0, "open", program.c_str(),
        arguments.empty() ? NULL : arguments.c_str(),
        NULL, SW_SHOW);
    return (long long)result > 32;
}

// --- NUEVAS FUNCIONES DE GESTIÓN DE PROCESOS ---

// Función para matar un proceso por nombre (Ej: "notepad.exe")
// Retorna: Cuántas instancias eliminó.
int kill_process_by_name(std::string process_name) {
    int killed_count = 0;

    // 1. Tomamos una "foto" (Snapshot) de todos los procesos actuales
    HANDLE hSnapshot = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (hSnapshot == INVALID_HANDLE_VALUE) return 0;

    PROCESSENTRY32 pe;
    pe.dwSize = sizeof(PROCESSENTRY32);

    // 2. Miramos el primer proceso de la foto
    if (Process32First(hSnapshot, &pe)) {
        do {
            // Convertimos el nombre del proceso a string para comparar
            // _stricmp compara sin importar mayúsculas/minúsculas
            if (_stricmp(pe.szExeFile, process_name.c_str()) == 0) {

                // 3. ¡ENCONTRADO! Abrimos el proceso con permiso de TERMINAR (Matar)
                HANDLE hProcess = OpenProcess(PROCESS_TERMINATE, FALSE, pe.th32ProcessID);
                if (hProcess != NULL) {
                    // 4. Ejecutamos la orden final
                    if (TerminateProcess(hProcess, 0)) {
                        killed_count++;
                    }
                    CloseHandle(hProcess);
                }
            }
            // 5. Pasamos al siguiente proceso de la lista
        } while (Process32Next(hSnapshot, &pe));
    }

    CloseHandle(hSnapshot);
    return killed_count;
}

// Función para listar procesos activos (Devuelve una lista a Python)
std::vector<std::string> get_running_processes() {
    std::vector<std::string> process_list;
    HANDLE hSnapshot = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);

    if (hSnapshot == INVALID_HANDLE_VALUE) return process_list;

    PROCESSENTRY32 pe;
    pe.dwSize = sizeof(PROCESSENTRY32);

    if (Process32First(hSnapshot, &pe)) {
        do {
            process_list.push_back(std::string(pe.szExeFile));
        } while (Process32Next(hSnapshot, &pe));
    }

    CloseHandle(hSnapshot);
    return process_list;
}

// --- NUEVAS FUNCIONES DE MONITOREO ---

// 1. Obtener estado de la RAM
py::dict get_memory_status() {
    MEMORYSTATUSEX memInfo;
    memInfo.dwLength = sizeof(MEMORYSTATUSEX);
    GlobalMemoryStatusEx(&memInfo);

    // Convertimos bytes a Megabytes (MB) para que sea legible
    // 1 MB = 1024 * 1024 bytes
    unsigned long long totalPhysMB = memInfo.ullTotalPhys / 1048576;
    unsigned long long availPhysMB = memInfo.ullAvailPhys / 1048576;
    
    py::dict info;
    info["total_mb"] = totalPhysMB;
    info["free_mb"] = availPhysMB;
    info["percent_used"] = memInfo.dwMemoryLoad; // Windows ya nos da el porcentaje calculado
    
    return info;
}

// 2. Obtener espacio en Disco C:
py::dict get_disk_status() {
    ULARGE_INTEGER freeBytesAvailableToCaller;
    ULARGE_INTEGER totalNumberOfBytes;
    ULARGE_INTEGER totalNumberOfFreeBytes;

    // Consultamos el disco C: (La raíz del sistema)
    GetDiskFreeSpaceExA("C:\\", 
        &freeBytesAvailableToCaller, 
        &totalNumberOfBytes, 
        &totalNumberOfFreeBytes
    );

    // Convertimos a Gigabytes (GB)
    // 1 GB = 1024 * 1024 * 1024 bytes
    double totalGB = (double)totalNumberOfBytes.QuadPart / 1073741824.0;
    double freeGB = (double)freeBytesAvailableToCaller.QuadPart / 1073741824.0;

    py::dict info;
    info["total_gb"] = totalGB;
    info["free_gb"] = freeGB;
    // Calculamos el porcentaje usado manualmente
    info["percent_used"] = ((totalGB - freeGB) / totalGB) * 100.0;

    return info;
}

// --- GESTIÓN DE ARCHIVOS (VERSIÓN UTF-8 BLINDADA) ---

std::vector<std::string> scan_directory(std::string path_str) {
    std::vector<std::string> files;

    try {
        // TRUCO 1: Input
        // Usamos u8path para decirle a C++: "Oye, el string que viene de Python es UTF-8"
        // Esto permite que lea rutas con tildes (Ej: C:\Usuarios\Jesús\Descargas)
        fs::path path = fs::u8path(path_str);

        if (fs::exists(path) && fs::is_directory(path)) {
            for (const auto& entry : fs::directory_iterator(path)) {
                if (entry.is_regular_file()) {
                    // TRUCO 2: Output
                    // Obtenemos el nombre en formato UTF-8 nativo
                    auto u8_filename = entry.path().filename().u8string();

                    // Convertimos ese formato raro a un std::string normal
                    // para que Pybind11 se lo pueda pasar a Python sin explotar
                    std::string final_name(u8_filename.begin(), u8_filename.end());

                    files.push_back(final_name);
                }
            }
        }
    }
    catch (const std::exception& e) {
        // Si algo falla (permisos, archivos corruptos), no explotamos.
        // Solo imprimimos el error en la consola negra y seguimos.
        std::cerr << "⚠️ Error en scan_directory: " << e.what() << std::endl;
    }

    return files;
}

// --- MÓDULO PRINCIPAL ---
PYBIND11_MODULE(ruth_backend, m) {
    m.doc() = "Módulo Service Desk Ruth v0.5";

    m.def("get_system_info", []() {
        py::dict info;
        info["pc_name"] = get_computer_name();
        info["user"] = get_user_name();
        return info;
        }, "Info del sistema");

    m.def("run_process", &run_process, "Ejecuta Apps");


    m.def("kill_process_by_name", &kill_process_by_name, "Elimina procesos por nombre");
    m.def("get_running_processes", &get_running_processes, "Lista todos los procesos activos");

    m.def("get_memory_status", &get_memory_status, "Obtiene el estado de la memoria RAM");
    m.def("get_disk_status", &get_disk_status, "Obtiene el estado del disco C:");

    m.def("scan_directory", &scan_directory, "Lista archivos en una ruta");
}