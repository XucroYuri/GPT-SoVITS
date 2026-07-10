@echo off
chcp 65001 >nul
setlocal EnableExtensions
cd /d "%~dp0"

set "PYTHON_EXECUTABLE=%cd%\py312\python.exe"
if not exist "%PYTHON_EXECUTABLE%" (
    echo [ERROR] 未找到内置 Python: %PYTHON_EXECUTABLE%
    pause
    exit /b 1
)

echo [INFO] 开始构建 GPT-SoVITS 绿色整合包...
"%PYTHON_EXECUTABLE%" -u tools\build_portable_package.py %*
set "EXIT_CODE=%ERRORLEVEL%"
if not "%EXIT_CODE%"=="0" (
    echo [ERROR] 打包失败，退出码: %EXIT_CODE%
    pause
    exit /b %EXIT_CODE%
)

echo [INFO] 打包流程结束。
pause
