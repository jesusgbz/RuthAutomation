#include <pybind11/pybind11.h>
#include <pybind11/stl.h> // <--- ¡ESTA ES LA CLAVE! Convierte std::vector a Python list
#include <windows.h>
#include <Lmcons.h>
#include <shellapi.h>
#include <tlhelp32.h> // <--- NUEVA LIBRERÍA: Para ver y matar procesos
#include <string>
#include <vector>
#include <iostream>
#include <wininet.h>
#include <mmdeviceapi.h>
#include <endpointvolume.h>
#pragma comment(lib, "Mmdevapi.lib") // Aseguramiento extra para el linker
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

// --- SIMULACIÓN DE TECLADO ---

// Función auxiliar para enviar una sola tecla
void send_key(WORD key, bool key_up = false) {
    INPUT input = { 0 };
    input.type = INPUT_KEYBOARD;
    input.ki.wVk = key;
    if (key_up) {
        input.ki.dwFlags = KEYEVENTF_KEYUP;
    }
    SendInput(1, &input, sizeof(INPUT));
}

// Escribe texto simulando pulsaciones de teclado
void type_text(std::string text) {
    for (char c : text) {
        INPUT input = { 0 };
        input.type = INPUT_KEYBOARD;
        input.ki.wScan = c;
        input.ki.dwFlags = KEYEVENTF_UNICODE;

        SendInput(1, &input, sizeof(INPUT)); // Presionar

        input.ki.dwFlags = KEYEVENTF_UNICODE | KEYEVENTF_KEYUP;
        SendInput(1, &input, sizeof(INPUT)); // Soltar

        // AJUSTE DE CALIDAD: Subimos a 50ms para garantizar que ninguna letra se pierda
        Sleep(70);
    }
}

// Presionar tecla ENTER (Para enviar formularios o comandos)
void press_enter() {
    send_key(VK_RETURN);       // Presionar
    send_key(VK_RETURN, true); // Soltar
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

// --- GESTIÓN DE VENTANAS ---

// Busca una ventana por parte de su título (ej: "Bloc de notas")
// Retorna: El "Handle" (Identificador único) de la ventana, o 0 si no la halla.
HWND find_window_by_title_part(std::string text_part) {
    HWND hCurrent = NULL;
    // Recorremos todas las ventanas de Windows
    do {
        hCurrent = FindWindowEx(NULL, hCurrent, NULL, NULL);
        char buffer[256];
        GetWindowTextA(hCurrent, buffer, 256);
        std::string title(buffer);

        // Si el título contiene el texto que buscamos (ignorando mayúsculas sería mejor, pero simple por ahora)
        if (title.length() > 0 && title.find(text_part) != std::string::npos) {
            return hCurrent; // ¡Encontrada!
        }
    } while (hCurrent != NULL);

    return NULL; // No encontrada
}

// Trae una ventana al frente
bool focus_window(std::string window_title_part) {
    HWND hWnd = find_window_by_title_part(window_title_part);
    if (hWnd) {
        // Restaurar si está minimizada
        ShowWindow(hWnd, SW_RESTORE);
        // Traer al frente
        SetForegroundWindow(hWnd);
        return true;
    }
    return false;
}

// Maximiza una ventana
bool maximize_window(std::string window_title_part) {
    HWND hWnd = find_window_by_title_part(window_title_part);
    if (hWnd) {
        ShowWindow(hWnd, SW_MAXIMIZE);
        return true;
    }
    return false;
}

// Cierra una ventana
bool close_window_by_title(std::string window_title_part) {
    HWND hWnd = find_window_by_title_part(window_title_part);
    if (hWnd) {
        // Enviamos mensaje de cerrar (Alt+F4 virtual)
        PostMessage(hWnd, WM_CLOSE, 0, 0);
        return true;
    }
    return false;
}

// --- CONTROL DEL MOUSE ---

// Mueve el cursor a una posición absoluta
void move_mouse(int x, int y) {
    // Convertimos coordenadas de píxeles a coordenadas absolutas de pantalla (0-65535)
    // Esto es necesario porque SendInput usa un sistema normalizado
    int screen_width = GetSystemMetrics(SM_CXSCREEN);
    int screen_height = GetSystemMetrics(SM_CYSCREEN);

    int abs_x = (x * 65535) / screen_width;
    int abs_y = (y * 65535) / screen_height;

    INPUT input = { 0 };
    input.type = INPUT_MOUSE;
    input.mi.dx = abs_x;
    input.mi.dy = abs_y;
    input.mi.dwFlags = MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE;

    SendInput(1, &input, sizeof(INPUT));
}

// Hace un clic simple
void mouse_click(bool is_right_click = false) {
    INPUT input = { 0 };
    input.type = INPUT_MOUSE;

    if (is_right_click) {
        input.mi.dwFlags = MOUSEEVENTF_RIGHTDOWN;
        SendInput(1, &input, sizeof(INPUT));
        input.mi.dwFlags = MOUSEEVENTF_RIGHTUP;
        SendInput(1, &input, sizeof(INPUT));
    }
    else {
        input.mi.dwFlags = MOUSEEVENTF_LEFTDOWN;
        SendInput(1, &input, sizeof(INPUT));
        input.mi.dwFlags = MOUSEEVENTF_LEFTUP;
        SendInput(1, &input, sizeof(INPUT));
    }
}

// Obtiene la posición actual del cursor (Retorna una lista [x, y])
std::vector<int> get_mouse_position() {
    POINT p;
    if (GetCursorPos(&p)) {
        return { p.x, p.y };
    }
    return { 0, 0 };
}

// --- DETECCIÓN DE TECLADO (INPUT SENSING) ---

// Verifica si una tecla específica está presionada FÍSICAMENTE en este instante
// key_code: Código virtual de la tecla (Ej: 0x1B es ESC)
bool is_key_pressed(int key_code) {
    // GetAsyncKeyState devuelve el estado en tiempo real.
    // Verificamos el bit más significativo (0x8000) que indica "Presionado".
    return (GetAsyncKeyState(key_code) & 0x8000) != 0;
}

// --- LIMPIEZA DE SISTEMA ---

// Borra un archivo específico
bool delete_file(std::string path_str) {
    try {
        fs::path path = fs::u8path(path_str);
        if (fs::exists(path) && fs::is_regular_file(path)) {
            // remove devuelve true si se borró, false si no
            return fs::remove(path);
        }
    }
    catch (const std::exception& e) {
        // Si el archivo está en uso (común en Temp), fallará. Es normal.
        // Solo lo ignoramos.
    }
    return false;
}

// --- SEGURIDAD Y TIEMPO ---

// Retorna los milisegundos que el sistema ha estado encendido
unsigned long long get_system_uptime_ms() {
    return GetTickCount64();
}

// Bloquea la sesión de Windows (Pantalla de Login)
// Equivalente a presionar Windows + L
bool lock_session() {
    return LockWorkStation();
}

// --- REDES ---

// Verifica si hay conexión real a internet
bool check_internet_connection() {
    // Intenta conectar a Google (puerto 80)
    // FLAG: 1 (FLAG_ICC_FORCE_CONNECTION)
    bool connected = InternetCheckConnectionA("http://www.google.com", 1, 0);
    return connected;
}


// --- CONTROL DE AUDIO (WASAPI) ---

// Cambia el volumen maestro (0.0 a 1.0)
// Ejemplo: 0.5 es 50%
bool set_master_volume(float level) {
    HRESULT hr;

    // 1. Inicializamos la librería COM (si no estaba ya)
    CoInitialize(NULL);

    IMMDeviceEnumerator* deviceEnumerator = NULL;
    IMMDevice* defaultDevice = NULL;
    IAudioEndpointVolume* endpointVolume = NULL;

    // 2. Obtenemos el enumerador de dispositivos
    hr = CoCreateInstance(__uuidof(MMDeviceEnumerator), NULL, CLSCTX_INPROC_SERVER, __uuidof(IMMDeviceEnumerator), (LPVOID*)&deviceEnumerator);
    if (FAILED(hr)) return false;

    // 3. Obtenemos las bocinas predeterminadas
    hr = deviceEnumerator->GetDefaultAudioEndpoint(eRender, eMultimedia, &defaultDevice);
    if (FAILED(hr)) { deviceEnumerator->Release(); return false; }

    // 4. Activamos el control de volumen
    hr = defaultDevice->Activate(__uuidof(IAudioEndpointVolume), CLSCTX_INPROC_SERVER, NULL, (LPVOID*)&endpointVolume);
    if (FAILED(hr)) { defaultDevice->Release(); deviceEnumerator->Release(); return false; }

    // 5. AJUSTAMOS EL VOLUMEN
    // Nos aseguramos que el nivel esté entre 0.0 y 1.0
    if (level < 0.0f) level = 0.0f;
    if (level > 1.0f) level = 1.0f;

    hr = endpointVolume->SetMasterVolumeLevelScalar(level, NULL);

    // 6. Limpieza de memoria (Vital en C++)
    endpointVolume->Release();
    defaultDevice->Release();
    deviceEnumerator->Release();

    return SUCCEEDED(hr);
}

// Silencia o reactiva el audio (Mute Toggle)
bool set_mute(bool mute) {
    CoInitialize(NULL);
    IMMDeviceEnumerator* deviceEnumerator = NULL;
    IMMDevice* defaultDevice = NULL;
    IAudioEndpointVolume* endpointVolume = NULL;

    CoCreateInstance(__uuidof(MMDeviceEnumerator), NULL, CLSCTX_INPROC_SERVER, __uuidof(IMMDeviceEnumerator), (LPVOID*)&deviceEnumerator);
    deviceEnumerator->GetDefaultAudioEndpoint(eRender, eMultimedia, &defaultDevice);
    defaultDevice->Activate(__uuidof(IAudioEndpointVolume), CLSCTX_INPROC_SERVER, NULL, (LPVOID*)&endpointVolume);

    // AJUSTAMOS EL MUTE
    endpointVolume->SetMute(mute, NULL);

    endpointVolume->Release();
    defaultDevice->Release();
    deviceEnumerator->Release();
    return true;
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

    m.def("type_text", &type_text, "Escribe texto simulado");
    m.def("press_enter", &press_enter, "Presiona la tecla Enter");
    
    m.def("focus_window", &focus_window, "Trae ventana al frente");
    m.def("maximize_window", &maximize_window, "Maximiza ventana");
    m.def("close_window_by_title", &close_window_by_title, "Cierra ventana");

    
    m.def("move_mouse", &move_mouse, "Mueve el cursor a X, Y");
    m.def("mouse_click", &mouse_click, "Hace clic (true para derecho)");

    m.def("get_mouse_position", &get_mouse_position, "Obtiene coords X, Y");
    m.def("is_key_pressed", &is_key_pressed, "Detecta si una tecla está presionada");
    m.def("delete_file", &delete_file, "Borra un archivo del sistema");

    m.def("get_system_uptime_ms", &get_system_uptime_ms, "Milisegundos desde el inicio");
    m.def("lock_session", &lock_session, "Bloquea la sesión de Windows");

    m.def("check_internet_connection", &check_internet_connection, "Verifica salida a internet");
    m.def("set_master_volume", &set_master_volume, "Pone volumen (0.0 a 1.0)");
    m.def("set_mute", &set_mute, "Silencia (True) o Reactiva (False)");

}