@echo off
setlocal EnableExtensions
chcp 65001 >nul
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
cd /d "%SCRIPT_DIR%"

if exist "%SCRIPT_DIR%\deploy.env.bat" call "%SCRIPT_DIR%\deploy.env.bat"

set "PYTHON_EXE="
if exist "%SCRIPT_DIR%\runtime\python.exe" set "PYTHON_EXE=%SCRIPT_DIR%\runtime\python.exe"
if not defined PYTHON_EXE if exist "%SCRIPT_DIR%\py312\python.exe" set "PYTHON_EXE=%SCRIPT_DIR%\py312\python.exe"
if not defined PYTHON_EXE if exist "%SCRIPT_DIR%\.venv\Scripts\python.exe" set "PYTHON_EXE=%SCRIPT_DIR%\.venv\Scripts\python.exe"

if defined PYTHON_EXE goto run_local_python
if defined GPTSOVITS_CONDA_ENV goto run_conda_python
goto no_python

:run_local_python
for %%I in ("%PYTHON_EXE%") do set "PYTHON_DIR=%%~dpI"
set "PATH=%PYTHON_DIR%;%SCRIPT_DIR%;%PATH%"
"%PYTHON_EXE%" -I "%SCRIPT_DIR%\webui.py" zh_CN
goto end

:run_conda_python
where conda >nul 2>nul
if errorlevel 1 goto conda_missing
conda run -n "%GPTSOVITS_CONDA_ENV%" python -I "%SCRIPT_DIR%\webui.py" zh_CN
goto end

:conda_missing
echo 未找到 conda，无法启动环境 %GPTSOVITS_CONDA_ENV%。
echo 请先安装 Miniforge/Anaconda，或重新运行 deploy.bat 选择复制/软链接可用 Python 环境。
pause
exit /b 1

:no_python
echo 未找到可用 Python 环境。
echo 请先运行 deploy.bat 完成部署，或放置 runtime\python.exe / py312\python.exe / .venv\Scripts\python.exe。
pause
exit /b 1

:end
pause
endlocal
