# Kokoro TTS - Portable Edition

A high-quality, portable text-to-speech application with multiple voices and languages. Kokoro TTS runs completely offline and is designed to be portable and easy to use.

## Features

- **High-Quality Voices**: Multiple natural-sounding voices in American English, British English, Italian, and more
- **Completely Self-Contained**: No need to install Python or any dependencies globally
- **Automatic CUDA Detection**: Automatically detects CUDA and installs the appropriate PyTorch version
- **Local Cache Storage**: All cache files are stored locally within the application directory
- **Voice Customization**: Upload custom voice files or create mixed voices by combining existing ones
- **Portable Design**: Can be moved between computers without reinstallation
- **User-Friendly Interface**: Simple web-based interface accessible through your browser

## System Requirements

- Windows 10 or later
- At least 4GB of RAM (8GB or more recommended)
- At least 2GB of free disk space
- NVIDIA GPU with CUDA support (optional, for faster processing)
- Internet connection (required only for first run to download models)

## Installation Options

### Standard Installation

1. Clone this github repo to any location on your computer
2. Run `install.bat` to set up the embedded Python and install all required dependencies
3. Wait for the installation to complete (this may take several minutes)
4. Run `run.bat` to start the application
   - The first time you run it, it will automatically download the required models
   - It will also detect if you have CUDA available and install the appropriate version of PyTorch

### One-Click Package

For users who want a simpler setup experience, the One-Click Package includes all dependencies pre-installed:

1. Download the [>>>`Kokoro-tts(one-click-package).zip`<<<](https://github.com/DrStr4Nge147/Kokoro-TTS-Portable/releases/download/latest/Kokoro-tts.one-click-package.zip)
2. Extract the zip file to any location on your computer
3. Run `run.bat` to start the application
4. **Important**: The first time you run the application, it requires an internet connection to download the voice models
5. After the initial run, the application can work completely offline

The One-Click Package includes:
- Embedded Python interpreter
- All required Python packages pre-installed
- Pre-configured environment for optimal performance
- Automatic GPU/CPU detection and configuration

## Usage

1. After starting the application with `run.bat`, it will automatically open in your web browser at http://127.0.0.1:7860
2. Enter the text you want to convert to speech in the text input area
3. Select a voice from the dropdown menu
4. Adjust the speech speed using the slider if needed
5. Click "Generate Speech" to create the audio
6. The generated audio will appear in the output section, where you can play or download it
7. All generated audio files are also saved in the `kokoro/outputs` folder

## Customization

### Custom Voices

You can upload custom voice files (.pt format) in the "Custom Voices" tab:

1. Navigate to the "Custom Voices" tab
2. Enter a name for your custom voice
3. Upload a .pt voice file
4. Click "Upload Voice"
5. Your custom voice will now appear in the voice dropdown menu with the prefix "👤 Custom:"

### Voice Mixer

Create new voices by mixing existing ones:

1. Navigate to the "Voice Mixer" tab
2. Use the checkboxes and sliders to select voices and their weights
3. Click "Update Formula" to generate the voice formula
4. Enter a name for your mixed voice
5. Optionally enter test text to hear the mixed voice
6. Click "Create Mixed Voice"
7. Your mixed voice will be available in the voice dropdown menu

## Voice Options

Kokoro TTS includes a variety of voices across different languages and styles:

- 🇺🇸 American English (female and male voices)
- 🇬🇧 British English (female and male voices)
- 🇮🇹 Italian (female and male voices)
- Additional specialty voices

Each voice has unique characteristics and is optimized for natural-sounding speech.

## Portability

After running the application once on your computer, you can:

1. Copy the entire folder to another computer or USB drive
2. Run `run.bat` directly (no need to run `install.bat` again)
3. The application will automatically detect the hardware capabilities of the new computer and configure itself accordingly

## Folder Structure

- `kokoro/` - Contains the application code
- `kokoro/outputs/` - Where generated audio files are saved
- `kokoro/custom_voices/` - Where custom voice files are stored
- `system/` - Contains the embedded Python and installed packages
- `system/cache/` - Where model files are stored locally
- `install.bat` - Script to set up the embedded Python and dependencies
- `run.bat` - Script to run the application
- `environment.bat` - Script to set up the environment variables

## Troubleshooting

### Common Issues

- **Models Not Found**: If you see errors about models not being found, ensure you have an internet connection for the first run to download the models.
- **CUDA Issues**: If you have a compatible NVIDIA GPU but the application runs in CPU mode, try running `run.bat` again. It will attempt to install the CUDA-compatible PyTorch version.
- **Browser Doesn't Open**: If the browser doesn't open automatically, manually navigate to http://127.0.0.1:7860 in your web browser.
- **Audio Not Playing**: Ensure your system's audio is working correctly and not muted.

### Installation Issues

1. Make sure you've run `install.bat` before trying to run the application (for standard installation)
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

### Runtime Issues

1. If the application crashes during runtime:
   - Check the console output for error messages
   - Try running the application again
2. If you see errors about missing DLLs:
   - Make sure the application folder contains all necessary files
   - Try running `install.bat` again to reinstall dependencies
3. If the application is slow:
   - If you have a GPU, make sure CUDA is properly detected
   - Close other resource-intensive applications
   - Try generating shorter text segments

## Moving or Copying the Application

This application is completely portable. You can:

- Move the entire folder to a different location on your computer
- Copy it to a USB drive to use on different computers
- Share it with others who don't have Python installed

No additional setup is required after moving - just run `run.bat` from the new location.

## Credits

Kokoro TTS is an open-source text-to-speech system with high-quality voices.

For more information, visit the original project repository.
