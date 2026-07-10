@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo [INFO] 开始训练.bat 已转到新的训练入口: 启动_训练WebUI.bat
call "%~dp0启动_训练WebUI.bat"
