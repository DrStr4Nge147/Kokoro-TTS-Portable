@echo off
setlocal enabledelayedexpansion

REM Get the current directory
set "KOKORO_ROOT=%~dp0"
set "KOKORO_ROOT=%KOKORO_ROOT:~0,-1%"

REM Set Python path
set "PYTHONHOME=%KOKORO_ROOT%\system"
set "PYTHONPATH=%KOKORO_ROOT%\system;%KOKORO_ROOT%\system\Lib;%KOKORO_ROOT%\system\Lib\site-packages"
set "PATH=%KOKORO_ROOT%\system;%KOKORO_ROOT%\system\Scripts;%PATH%"

REM Set cache directories to be local to the application
set "HF_HOME=%KOKORO_ROOT%\system\cache\HF_HOME"
set "TORCH_HOME=%KOKORO_ROOT%\system\cache\TORCH_HOME"
set "TRANSFORMERS_CACHE=%KOKORO_ROOT%\system\cache\HF_HOME"
set "HF_DATASETS_CACHE=%KOKORO_ROOT%\system\cache\HF_HOME"
set "HF_HUB_CACHE=%KOKORO_ROOT%\system\cache\HF_HOME"
set "HUGGINGFACE_HUB_CACHE=%KOKORO_ROOT%\system\cache\HF_HOME"
set "HF_ASSETS_CACHE=%KOKORO_ROOT%\system\cache\HF_HOME"
set "HUGGINGFACE_ASSETS_CACHE=%KOKORO_ROOT%\system\cache\HF_HOME"
set "HF_HUB_DISABLE_SYMLINKS_WARNING=1"
set "HF_HUB_ENABLE_HF_TRANSFER=0"

REM Set phonemizer to use local directory for espeak-ng.dll
set "PHONEMIZER_ESPEAK_LIBRARY=%KOKORO_ROOT%\system\Lib\site-packages\espeakng_loader\espeak-ng.dll"

REM Create cache directories if they don't exist
if not exist "%KOKORO_ROOT%\system\cache" mkdir "%KOKORO_ROOT%\system\cache"
if not exist "%HF_HOME%" mkdir "%HF_HOME%"
if not exist "%TORCH_HOME%" mkdir "%TORCH_HOME%"

REM Set temporary directory to be local
set "TEMP=%KOKORO_ROOT%\system\temp"
set "TMP=%KOKORO_ROOT%\system\temp"

REM Create temp directory if it doesn't exist
if not exist "%KOKORO_ROOT%\system\temp" mkdir "%KOKORO_ROOT%\system\temp"

echo Environment variables set for Kokoro TTS
