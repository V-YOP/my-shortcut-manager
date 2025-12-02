// gsm.cpp - 无窗口 Python 启动器
#include <windows.h>
#include <string>

int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow) {
    // 获取当前 exe 所在目录
    char exePath[MAX_PATH];
    GetModuleFileNameA(NULL, exePath, MAX_PATH);

    std::string path(exePath);
    size_t lastSlash = path.find_last_of("\\/");
    if (lastSlash != std::string::npos) {
        path = path.substr(0, lastSlash + 1); // 保留最后的反斜杠
    }
    path += "gsm.py";

    // 构造命令：使用 pythonw 避免控制台
    std::string cmd = "pythonw \"" + path + "\"";

    // 使用 SW_HIDE 隐藏窗口，并异步启动（不等待）
    STARTUPINFOA si = { sizeof(STARTUPINFOA) };
    PROCESS_INFORMATION pi;
    si.dwFlags = STARTF_USESHOWWINDOW;
    si.wShowWindow = SW_HIDE; // 关键：隐藏窗口

    BOOL result = CreateProcessA(
        NULL,               // lpApplicationName
        &cmd[0],            // lpCommandLine（必须可修改，所以不能用 const char*）
        NULL,               // lpProcessAttributes
        NULL,               // lpThreadAttributes
        FALSE,              // bInheritHandles
        CREATE_NO_WINDOW,   // dwCreationFlags（额外确保无窗口）
        NULL,               // lpEnvironment
        NULL,               // lpCurrentDirectory
        &si,                // lpStartupInfo
        &pi                 // lpProcessInformation
    );

    if (result) {
        // 不等待，立即退出启动器
        CloseHandle(pi.hProcess);
        CloseHandle(pi.hThread);
    }

    return 0;
}
