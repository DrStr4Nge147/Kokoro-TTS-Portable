# Kokoro TTS - Portable Edition

This is a portable, self-contained version of Kokoro TTS that can run on any Windows computer without requiring a global Python installation.

## Features

- Completely self-contained - no need to install Python or any dependencies globally
- Automatically detects CUDA and installs the appropriate PyTorch version
- All cache files are stored locally within the application directory
- Easy to use with simple batch scripts for installation and running

## System Requirements

- Windows 10 or later
- At least 4GB of RAM (8GB or more recommended)
- At least 2GB of free disk space
- NVIDIA GPU with CUDA support (optional, for faster processing)

## Installation

1. Download and extract this folder to any location on your computer
2. Run `install.bat` to set up the embedded Python and install all required dependencies
3. Wait for the installation to complete (this may take several minutes)
4. The installation process will automatically detect if you have CUDA available and install the appropriate version of PyTorch

## Usage

1. After installation, run `run.bat` to start the application
2. The application will open in your web browser at http://127.0.0.1:7860
3. Use the interface to generate text-to-speech with various voices

## Folder Structure

- `kokoro/` - Contains the application code and dependencies
- `system/` - Contains the embedded Python and installed packages
- `outputs/` - Where generated audio files are saved
- `custom_voices/` - Where custom voice files are stored
- `install.bat` - Script to set up the embedded Python and dependencies
- `run.bat` - Script to run the application
- `environment.bat` - Script to set up the environment variables

## Troubleshooting

If you encounter any issues:

1. Make sure you've run `install.bat` before trying to run the application
2. Check that you have enough disk space (at least 2GB free)
3. If you have an NVIDIA GPU but CUDA is not being detected:
   - Make sure you have the latest NVIDIA drivers installed
   - Check if CUDA is properly installed by running `nvcc --version` in a command prompt
4. If the application crashes during installation:
   - Try running the installation again
   - If specific packages fail to install, you can try installing them manually by opening a command prompt in the application directory and running:
     ```
     system\python.exe -m pip install [package_name]
     ```
5. If the application crashes during runtime:
   - Check the console output for error messages
   - Try running the application again

## Moving or Copying the Application

This application is completely portable. You can:

- Move the entire folder to a different location on your computer
- Copy it to a USB drive to use on different computers
- Share it with others who don't have Python installed

No additional setup is required after moving - just run `run.bat` from the new location.

## Credits

Kokoro TTS is an open-source text-to-speech system with high-quality voices.

For more information, visit the original project repository.
