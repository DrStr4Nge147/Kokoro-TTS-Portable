@echo off
setlocal enabledelayedexpansion

echo ========================================
echo Kokoro TTS - Running Application
echo ========================================
echo.

REM Check if system directory exists
if not exist system (
    echo Error: System directory not found.
    echo Please run install.bat first to set up the application.
    pause
    exit /b 1
)

REM Set environment variables first to ensure models are downloaded to the correct location
call environment.bat

REM Set additional environment variables for better portability
set PYTHONPATH=%~dp0
set PYTHONHOME=%~dp0system
set PHONEMIZER_ESPEAK_LIBRARY=%~dp0system\Lib\site-packages\espeakng_loader\espeak-ng.dll

REM Create system cache directory structure if it doesn't exist
if not exist system\cache (
    echo Creating system cache directory...
    mkdir system\cache
    mkdir system\cache\HF_HOME
    mkdir system\cache\HF_HOME\hub
    mkdir system\cache\TORCH_HOME
    echo System cache directory created.
)

REM Remove any root cache directory if it exists (to avoid confusion)
if exist cache (
    echo Removing root cache directory...
    rmdir /s /q cache
    echo Root cache directory removed.
)

REM First, try to copy models from the global cache to the local cache
echo Checking if models exist in global cache and copying them to local cache...
if exist copy_models_from_global.py (
    system\python.exe copy_models_from_global.py
)

REM Create a small Python script to ensure models are downloaded to the project directory
echo import os > "%TEMP%\ensure_local_models.py"
echo import sys >> "%TEMP%\ensure_local_models.py"
echo from huggingface_hub import hf_hub_download >> "%TEMP%\ensure_local_models.py"
echo # Force environment variables in the script >> "%TEMP%\ensure_local_models.py"
echo os.environ["HF_HOME"] = r"%KOKORO_ROOT%\system\cache\HF_HOME" >> "%TEMP%\ensure_local_models.py"
echo os.environ["TORCH_HOME"] = r"%KOKORO_ROOT%\system\cache\TORCH_HOME" >> "%TEMP%\ensure_local_models.py"
echo os.environ["TRANSFORMERS_CACHE"] = r"%KOKORO_ROOT%\system\cache\HF_HOME" >> "%TEMP%\ensure_local_models.py"
echo os.environ["HF_DATASETS_CACHE"] = r"%KOKORO_ROOT%\system\cache\HF_HOME" >> "%TEMP%\ensure_local_models.py"
echo os.environ["HF_HUB_CACHE"] = r"%KOKORO_ROOT%\system\cache\HF_HOME" >> "%TEMP%\ensure_local_models.py"
echo os.environ["HUGGINGFACE_HUB_CACHE"] = r"%KOKORO_ROOT%\system\cache\HF_HOME" >> "%TEMP%\ensure_local_models.py"
echo os.environ["HF_ASSETS_CACHE"] = r"%KOKORO_ROOT%\system\cache\HF_HOME" >> "%TEMP%\ensure_local_models.py"
echo os.environ["HUGGINGFACE_ASSETS_CACHE"] = r"%KOKORO_ROOT%\system\cache\HF_HOME" >> "%TEMP%\ensure_local_models.py"
echo # Override huggingface_hub constants >> "%TEMP%\ensure_local_models.py"
echo try: >> "%TEMP%\ensure_local_models.py"
echo     from huggingface_hub import constants >> "%TEMP%\ensure_local_models.py"
echo     constants.HF_HUB_CACHE = os.environ["HF_HOME"] >> "%TEMP%\ensure_local_models.py"
echo     constants.HF_HOME = os.environ["HF_HOME"] >> "%TEMP%\ensure_local_models.py"
echo     constants.HUGGINGFACE_HUB_CACHE = os.environ["HF_HOME"] >> "%TEMP%\ensure_local_models.py"
echo     constants.hf_cache_home = os.environ["HF_HOME"] >> "%TEMP%\ensure_local_models.py"
echo     constants.default_cache_path = os.path.join(os.environ["HF_HOME"], "hub") >> "%TEMP%\ensure_local_models.py"
echo     print("Successfully overrode huggingface_hub cache constants") >> "%TEMP%\ensure_local_models.py"
echo except Exception as e: >> "%TEMP%\ensure_local_models.py"
echo     print(f"Warning: Could not override huggingface_hub cache constants: {str(e)}") >> "%TEMP%\ensure_local_models.py"
echo # Verify environment variables >> "%TEMP%\ensure_local_models.py"
echo print("HF_HOME set to:", os.environ.get("HF_HOME", "Not set")) >> "%TEMP%\ensure_local_models.py"
echo print("TRANSFORMERS_CACHE set to:", os.environ.get("TRANSFORMERS_CACHE", "Not set")) >> "%TEMP%\ensure_local_models.py"
echo # Try to download the model and config to ensure they're in the local cache >> "%TEMP%\ensure_local_models.py"
echo try: >> "%TEMP%\ensure_local_models.py"
echo     print("Ensuring model files are in local cache...") >> "%TEMP%\ensure_local_models.py"
echo     config_path = hf_hub_download(repo_id="hexgrad/Kokoro-82M", filename="config.json", local_dir=r"%KOKORO_ROOT%\system\cache\HF_HOME\hub\models--hexgrad--Kokoro-82M", local_dir_use_symlinks=False) >> "%TEMP%\ensure_local_models.py"
echo     model_path = hf_hub_download(repo_id="hexgrad/Kokoro-82M", filename="kokoro-v1_0.pth", local_dir=r"%KOKORO_ROOT%\system\cache\HF_HOME\hub\models--hexgrad--Kokoro-82M", local_dir_use_symlinks=False) >> "%TEMP%\ensure_local_models.py"
echo     print("Config downloaded to:", config_path) >> "%TEMP%\ensure_local_models.py"
echo     print("Model downloaded to:", model_path) >> "%TEMP%\ensure_local_models.py"
echo     # Verify the files were downloaded to the correct location >> "%TEMP%\ensure_local_models.py"
echo     expected_path = r"%KOKORO_ROOT%\system\cache\HF_HOME" >> "%TEMP%\ensure_local_models.py"
echo     if expected_path not in config_path: >> "%TEMP%\ensure_local_models.py"
echo         print(f"WARNING: Config was not downloaded to the expected location!") >> "%TEMP%\ensure_local_models.py"
echo     if expected_path not in model_path: >> "%TEMP%\ensure_local_models.py"
echo         print(f"WARNING: Model was not downloaded to the expected location!") >> "%TEMP%\ensure_local_models.py"
echo except Exception as e: >> "%TEMP%\ensure_local_models.py"
echo     print("Error downloading model files:", e) >> "%TEMP%\ensure_local_models.py"
echo     # Continue anyway as the app might work with existing files >> "%TEMP%\ensure_local_models.py"

REM Run the script to ensure models are downloaded to the project directory
echo Ensuring models are in the local project directory...
system\python.exe "%TEMP%\ensure_local_models.py"
del "%TEMP%\ensure_local_models.py"

REM Run the application directly
echo Starting Kokoro TTS...
system\python.exe kokoro\app.py

echo.
echo ========================================
echo Application closed.
echo ========================================

pause
