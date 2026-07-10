@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo [INFO] 运行_统一推理WebUI.bat 已转到新的推理入口: 启动_推理WebUI.bat
call "%~dp0启动_推理WebUI.bat"
