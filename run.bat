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

REM Check if Python is installed in the system directory
if not exist system\python.exe (
    echo Error: Python executable not found in system directory.
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

REM Check if PyTorch is already installed
echo Checking if PyTorch is already installed...
system\python.exe -c "import torch; print('PyTorch is already installed. Version:', torch.__version__); print('CUDA Available:', torch.cuda.is_available()); exit(0)" > "%TEMP%\pytorch_check.txt" 2>&1
set PYTORCH_INSTALLED=0
set PYTORCH_CUDA_INSTALLED=0

REM Check if the import was successful (exit code 0)
if %ERRORLEVEL% EQU 0 (
    set PYTORCH_INSTALLED=1
    type "%TEMP%\pytorch_check.txt"

    REM Check if CUDA is available in PyTorch
    findstr /C:"CUDA Available: True" "%TEMP%\pytorch_check.txt" > nul
    if not errorlevel 1 (
        set PYTORCH_CUDA_INSTALLED=1
        echo CUDA support detected in PyTorch.
    ) else (
        echo PyTorch is installed but without CUDA support.
    )
) else (
    echo PyTorch is not installed.
)

REM Check for CUDA availability on the system
echo Checking for CUDA availability...
set CUDA_AVAILABLE=0

REM Check if nvidia-smi is available
where nvidia-smi > nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo NVIDIA GPU detected via nvidia-smi.
    set CUDA_AVAILABLE=1
) else (
    REM Check if nvcc is available
    where nvcc > nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo CUDA toolkit found via nvcc.
        set CUDA_AVAILABLE=1
    ) else (
        REM Check registry for NVIDIA driver
        reg query "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\nvlddmkm" > nul 2>&1
        if %ERRORLEVEL% EQU 0 (
            echo NVIDIA driver found in registry.
            set CUDA_AVAILABLE=1
        ) else (
            echo No CUDA support detected on this system.
        )
    )
)

REM Install or upgrade PyTorch based on the checks
if %PYTORCH_INSTALLED% EQU 0 (
    echo Installing PyTorch...

    if %CUDA_AVAILABLE% EQU 1 (
        echo Installing PyTorch with CUDA support...
        system\python.exe -m pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

        REM Verify CUDA is available in PyTorch
        echo Verifying CUDA installation...
        system\python.exe -c "import torch; print('CUDA Available after installation:', torch.cuda.is_available()); exit(0 if torch.cuda.is_available() else 1)" > "%TEMP%\cuda_verify.txt" 2>&1

        if %ERRORLEVEL% NEQ 0 (
            echo CUDA installation verification failed. Falling back to CPU version...
            echo Uninstalling current PyTorch...
            system\python.exe -m pip uninstall -y torch torchvision torchaudio
            echo Installing PyTorch CPU version...
            system\python.exe -m pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
        ) else (
            type "%TEMP%\cuda_verify.txt"
            echo CUDA installation verified successfully.
        )
    ) else (
        echo Installing PyTorch CPU version...
        system\python.exe -m pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
    )
) else (
    REM Check if we need to upgrade PyTorch to use CUDA
    if %PYTORCH_CUDA_INSTALLED% EQU 0 (
        if %CUDA_AVAILABLE% EQU 1 (
            echo PyTorch is installed but without CUDA support. Upgrading to CUDA version...
            echo Uninstalling current PyTorch...
            system\python.exe -m pip uninstall -y torch torchvision torchaudio

            echo Installing PyTorch with CUDA support...
            system\python.exe -m pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

            REM Verify CUDA is available in PyTorch
            echo Verifying CUDA installation...
            system\python.exe -c "import torch; print('CUDA Available after upgrade:', torch.cuda.is_available()); exit(0 if torch.cuda.is_available() else 1)" > "%TEMP%\cuda_verify.txt" 2>&1

            if %ERRORLEVEL% NEQ 0 (
                echo CUDA installation verification failed. Falling back to CPU version...
                echo Installing PyTorch CPU version...
                system\python.exe -m pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
            ) else (
                type "%TEMP%\cuda_verify.txt"
                echo CUDA installation verified successfully.
            )
        ) else (
            echo No CUDA support detected on this system. Using CPU-only PyTorch.
        )
    ) else (
        echo PyTorch is already installed with CUDA support. Continuing...
    )
)

REM Final verification of PyTorch installation
echo Final verification of PyTorch installation...
system\python.exe -c "import torch; print('PyTorch installed successfully. Version:', torch.__version__); print('CUDA Available:', torch.cuda.is_available()); print('CUDA Version:', torch.version.cuda if torch.cuda.is_available() else 'N/A (CPU only)')"

REM Clean up temporary files
del "%TEMP%\pytorch_check.txt" 2>nul
del "%TEMP%\cuda_verify.txt" 2>nul

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

REM Create a marker file to indicate that models have been downloaded
set MODEL_PATH=%KOKORO_ROOT%\system\cache\HF_HOME\hub\models--hexgrad--Kokoro-82M
set MARKER_FILE=%MODEL_PATH%\DOWNLOAD_COMPLETE

if exist "%MODEL_PATH%" (
    if not exist "%MARKER_FILE%" (
        echo Creating marker file to indicate models are downloaded...
        echo Models downloaded successfully > "%MARKER_FILE%"
        echo Marker file created.
    ) else (
        echo Marker file already exists, using cached models.
    )
) else (
    echo Model directory does not exist yet, will be created on first run.
)

REM Run the application directly
echo Starting Kokoro TTS...
echo The application will automatically open in your web browser when ready...
system\python.exe kokoro\app.py

echo.
echo ========================================
echo Application closed.
echo ========================================

pause
