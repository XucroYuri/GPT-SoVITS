@echo off
chcp 65001 >nul
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
cd /d "%SCRIPT_DIR%"

powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%\deploy.ps1"
if errorlevel 1 (
    echo.
    echo 部署失败，请查看上方错误信息。
    pause
    exit /b 1
)

echo.
pause
