@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo [INFO] 运行_自动开启接口服务.bat 已转到新的 API 入口: 启动_API服务.bat
call "%~dp0启动_API服务.bat"
