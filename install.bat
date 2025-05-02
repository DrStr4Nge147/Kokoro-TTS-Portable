@echo off
setlocal enabledelayedexpansion

echo ========================================
echo Kokoro TTS - Installation Script
echo ========================================
echo.

REM Create system directory if it doesn't exist
if not exist system (
    echo Creating system directory...
    mkdir system
) else (
    echo System directory already exists.
)

REM Download Python 3.10.11 embeddable package
echo Downloading Python 3.10.11 embeddable package...
powershell -Command "& {Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.10.11/python-3.10.11-embed-amd64.zip' -OutFile 'python-3.10.11-embed-amd64.zip'}"

REM Extract Python to system directory
echo Extracting Python to system directory...
powershell -Command "& {Expand-Archive -Path 'python-3.10.11-embed-amd64.zip' -DestinationPath 'system' -Force}"

REM Remove the zip file
echo Cleaning up...
del python-3.10.11-embed-amd64.zip

REM Uncomment the import site line in python310._pth
echo Enabling site-packages...
powershell -Command "& {(Get-Content 'system\python310._pth') -replace '#import site', 'import site' | Set-Content 'system\python310._pth'}"

REM Download get-pip.py
echo Downloading pip installer...
powershell -Command "& {Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile 'system\get-pip.py'}"

REM Install pip
echo Installing pip...
system\python.exe system\get-pip.py

REM Create necessary directories
echo Creating necessary directories...
mkdir system\cache
mkdir system\temp
mkdir kokoro\outputs
mkdir kokoro\custom_voices

REM Set environment variables for the installation process
call environment.bat

REM Check for CUDA availability
echo Checking for CUDA availability...
set CUDA_AVAILABLE=0

REM Check if nvidia-smi is available (simpler check for NVIDIA GPU)
where nvidia-smi >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo NVIDIA GPU detected. Will install PyTorch with CUDA support.
    set CUDA_AVAILABLE=1
) else (
    REM Try alternative method - check for nvcc
    where nvcc >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo CUDA toolkit found. Will install PyTorch with CUDA support.
        set CUDA_AVAILABLE=1
    ) else (
        REM Try one more method - check for NVIDIA driver in registry
        reg query "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\nvlddmkm" >nul 2>&1
        if %ERRORLEVEL% EQU 0 (
            echo NVIDIA driver found in registry. Will install PyTorch with CUDA support.
            set CUDA_AVAILABLE=1
        ) else (
            echo CUDA not detected. Will install CPU-only version of PyTorch.
        )
    )
)

REM Install PyTorch based on CUDA availability
echo Installing PyTorch...
if %CUDA_AVAILABLE% EQU 1 (
    echo Installing PyTorch with CUDA support...

    REM Install PyTorch with CUDA support
    echo Installing PyTorch with CUDA 12.1 support...
    system\python.exe -m pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

    REM Verify CUDA is available in PyTorch
    echo Verifying CUDA installation...
    system\python.exe -c "try: import torch; cuda_available = torch.cuda.is_available(); print('CUDA Available:', cuda_available); print('CUDA Version:', torch.version.cuda if cuda_available else 'N/A'); exit(0 if cuda_available else 1)\nexcept ImportError: print('PyTorch not installed properly'); exit(1)"

    if %ERRORLEVEL% NEQ 0 (
        echo CUDA installation verification failed. Falling back to CPU version...
        echo Uninstalling current PyTorch...
        system\python.exe -m pip uninstall -y torch torchvision torchaudio
        echo Installing PyTorch CPU version...
        system\python.exe -m pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
        echo Verification of CPU installation...
        system\python.exe -c "try: import torch; print('Using CPU-only PyTorch:', not torch.cuda.is_available())\nexcept ImportError: print('PyTorch not installed properly')"
    ) else (
        echo CUDA installation verified successfully.
    )
) else (
    echo Installing PyTorch CPU version...
    system\python.exe -m pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

    REM Verify CPU-only installation
    echo Verifying CPU installation...
    system\python.exe -c "try: import torch; print('Using CPU-only PyTorch:', not torch.cuda.is_available())\nexcept ImportError: print('PyTorch not installed properly')"
)

REM Install core dependencies first
echo Installing core dependencies...
system\python.exe -m pip install --upgrade pip
system\python.exe -m pip install numpy scipy tqdm wheel setuptools

REM Install required packages one by one to avoid dependency issues
echo Installing required packages...
system\python.exe -m pip install huggingface-hub
system\python.exe -m pip install pydub
system\python.exe -m pip install soundfile
system\python.exe -m pip install gradio
system\python.exe -m pip install transformers
system\python.exe -m pip install accelerate
system\python.exe -m pip install diffusers
system\python.exe -m pip install espeakng-loader
system\python.exe -m pip install phonemizer-fork
REM Install docopt manually first to avoid circular dependency issue
echo Installing docopt dependency...

REM Create a simple docopt module to bypass the circular dependency
echo Creating temporary docopt module...
if not exist system\Lib\site-packages (
    mkdir system\Lib\site-packages
)
if not exist system\Lib\site-packages\docopt (
    mkdir system\Lib\site-packages\docopt
)
echo __version__ = '0.6.2' > system\Lib\site-packages\docopt\__init__.py

REM Now install docopt
system\python.exe -m pip install --no-cache-dir docopt==0.6.2

REM Check if docopt installation was successful
system\python.exe -c "import docopt; print('Docopt version:', docopt.__version__)" > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Docopt installation failed, trying alternative method...

    REM Try installing with --no-deps
    echo Trying to install docopt with --no-deps...
    system\python.exe -m pip install --no-deps docopt==0.6.2

    REM Check again
    system\python.exe -c "import docopt; print('Docopt version:', docopt.__version__)" > nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo Still failed, trying to install from wheel...

        REM Try installing from wheel
        echo Downloading docopt wheel...
        powershell -Command "& {Invoke-WebRequest -Uri 'https://files.pythonhosted.org/packages/a2/55/8f8cab2afd404cf578136ef2cc5dfb50baa1761b68c9da1fb1e4eed343c9/docopt-0.6.2-py2.py3-none-any.whl' -OutFile 'docopt-0.6.2-py2.py3-none-any.whl'}"

        echo Installing docopt from wheel...
        system\python.exe -m pip install --no-deps docopt-0.6.2-py2.py3-none-any.whl

        REM Clean up
        del docopt-0.6.2-py2.py3-none-any.whl
    )
)

REM Install num2words (which depends on docopt)
echo Installing num2words dependency...
system\python.exe -m pip install num2words

REM Now install kokoro and misaki
echo Installing kokoro...
system\python.exe -m pip install kokoro

echo Installing misaki with English support...
system\python.exe -m pip install "misaki[en]" --no-deps

REM Check if misaki installation was successful
system\python.exe -c "import misaki" > nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Misaki installed successfully.

    REM Install remaining dependencies for misaki[en]
    echo Installing additional dependencies for misaki...
    system\python.exe -m pip install spacy
    system\python.exe -m pip install spacy-curated-transformers
) else (
    echo Misaki[en] installation failed, falling back to basic misaki...
    system\python.exe -m pip install misaki
)

echo.
echo ========================================
echo Installation complete!
echo Run the application using run.bat
echo ========================================

pause
