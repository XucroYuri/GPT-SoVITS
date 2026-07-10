@echo off
chcp 65001 >nul
setlocal EnableExtensions
cd /d "%~dp0"

set "GRADIO_TEMP_DIR=%cd%\tmp\"
set "PYTHON_PATH=%cd%\py312\"
set "PYTHON_EXECUTABLE=%PYTHON_PATH%\python.exe"
set "PYTHONEXECUTABLE=%PYTHON_EXECUTABLE%"
set "PYTHONWEXECUTABLE=%PYTHON_PATH%pythonw.exe"
set "PYTHONW_EXECUTABLE=%PYTHON_PATH%pythonw.exe"
set "PYTHON_BIN_PATH=%PYTHON_EXECUTABLE%"
set "PYTHON_LIB_PATH=%PYTHON_PATH%\Lib\site-packages"
set "DS_BUILD_AIO=0"
set "DS_BUILD_SPARSE_ATTN=0"
set "PYTHONHOME="
set "PYTHONPATH="
set "CU_PATH=%PYTHON_PATH%\Lib\site-packages\torch\lib"
set "cuda_PATH=%PYTHON_PATH%\Library\bin"
set "FFMPEG_PATH=%cd%\py312\ffmpeg\bin"
set "PATH=%PYTHON_PATH%;%PYTHON_PATH%\Scripts;%FFMPEG_PATH%;%CU_PATH%;%cuda_PATH%;%PATH%"
set "HF_ENDPOINT=https://hf-mirror.com"
set "HF_HOME=%CD%\hf_download"
set "TRANSFORMERS_CACHE=%CD%\tf_download"
set "XFORMERS_FORCE_DISABLE_TRITON=1"
set "GPT_SOVITS_PORTABLE_MODE=1"

if not exist "logs\startup" mkdir "logs\startup"
set "STAMP=%DATE:~-10%-%TIME%"
set "STAMP=%STAMP:/=-%"
set "STAMP=%STAMP::=-%"
set "STAMP=%STAMP:.=-%"
set "STAMP=%STAMP: =0%"
set "STAMP=%STAMP:,=-%"
set "LOG_FILE=%cd%\logs\startup\train-%STAMP%.log"

echo [INFO] 训练 WebUI 启动预检，日志: %LOG_FILE%
"%PYTHON_EXECUTABLE%" -u tools\startup_check.py --mode train >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    type "%LOG_FILE%"
    echo [ERROR] 预检失败，请按上方提示修复后重试。
    pause
    exit /b 1
)

echo [INFO] 训练 WebUI: http://127.0.0.1:9874/
echo [INFO] 训练 WebUI: http://127.0.0.1:9874/ >> "%LOG_FILE%"
"%PYTHON_EXECUTABLE%" -u tools\run_with_bootstrap.py -- webui.py zh_CN >> "%LOG_FILE%" 2>&1
pause
