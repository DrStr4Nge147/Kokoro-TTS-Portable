import os
import sys
import subprocess
import platform
import shutil
import importlib.util

def is_package_installed(package_name):
    """Check if a package is installed."""
    return importlib.util.find_spec(package_name) is not None

def check_cuda_available():
    """Check if CUDA is available on the system."""
    try:
        # Try to import torch first
        if not is_package_installed("torch"):
            print("PyTorch not installed. Will install appropriate version.")
            return False

        import torch
        return torch.cuda.is_available()
    except ImportError:
        print("PyTorch not installed. Will install appropriate version.")
        return False
    except Exception as e:
        print(f"Error checking CUDA availability: {e}")
        return False

def get_cuda_version():
    """Get the CUDA version if available."""
    try:
        # Try to run nvcc --version to get CUDA version
        result = subprocess.run(["nvcc", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            # Parse the output to get the CUDA version
            output = result.stdout
            import re
            match = re.search(r"release (\d+\.\d+)", output)
            if match:
                return match.group(1)
    except:
        pass

    # If we can't determine the version, check if we can detect CUDA through torch
    try:
        if is_package_installed("torch"):
            import torch
            if torch.cuda.is_available():
                return torch.version.cuda
    except:
        pass

    return None

def install_pytorch(cuda_available=False):
    """Install the appropriate PyTorch version based on CUDA availability."""
    print("Installing PyTorch...")

    # Get the Python executable path
    python_exe = sys.executable

    if cuda_available:
        cuda_version = get_cuda_version()
        print(f"CUDA detected (version: {cuda_version}). Installing PyTorch with CUDA support...")

        # Map CUDA version to PyTorch CUDA package version
        cuda_map = {
            "11.0": "cu110",
            "11.1": "cu111",
            "11.2": "cu112",
            "11.3": "cu113",
            "11.4": "cu114",
            "11.5": "cu115",
            "11.6": "cu116",
            "11.7": "cu117",
            "11.8": "cu118",
            "12.0": "cu120",
            "12.1": "cu121",
            "12.2": "cu122",
            "12.3": "cu123",
            "12.4": "cu124"
        }

        # Default to latest supported version if we can't determine the version
        cuda_pkg = "cu124"

        # If we detected a CUDA version, map it to the appropriate package
        if cuda_version:
            major_minor = ".".join(cuda_version.split(".")[:2])
            cuda_pkg = cuda_map.get(major_minor, "cu124")

        # Install PyTorch with CUDA support
        cmd = [
            python_exe, "-m", "pip", "install",
            "torch", "torchvision", "torchaudio",
            "--index-url", f"https://download.pytorch.org/whl/{cuda_pkg}"
        ]
    else:
        print("CUDA not detected. Installing PyTorch CPU version...")
        # Install PyTorch CPU version
        cmd = [
            python_exe, "-m", "pip", "install",
            "torch", "torchvision", "torchaudio"
        ]

    # Run the installation command
    subprocess.check_call(cmd)
    print("PyTorch installation complete.")

def install_dependencies():
    """Install all required dependencies."""
    print("Installing dependencies...")

    # Get the Python executable path
    python_exe = sys.executable

    # Get the requirements.txt file path
    requirements_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "requirements.txt")

    # Install dependencies from requirements.txt
    subprocess.check_call([
        python_exe, "-m", "pip", "install", "-r", requirements_path
    ])

    print("Dependencies installation complete.")

def run_app():
    """Run the Kokoro TTS application."""
    print("Starting Kokoro TTS application...")

    # Get the app.py file path
    app_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.py")

    # Run the application
    subprocess.check_call([sys.executable, app_path])

def main():
    """Main function to run the launcher."""
    print("Kokoro TTS Launcher")
    print("===================")

    # Check if PyTorch is already installed
    if not is_package_installed("torch"):
        # Check if CUDA is available
        cuda_available = check_cuda_available()
        if cuda_available:
            print("CUDA is available on this system.")
        else:
            print("CUDA is not available. Will use CPU mode.")

        # Install PyTorch with appropriate support
        install_pytorch(cuda_available)
    else:
        print("PyTorch is already installed.")

        # Check if CUDA is available with the installed PyTorch
        import torch
        if torch.cuda.is_available():
            print(f"CUDA is available (PyTorch CUDA version: {torch.version.cuda})")
        else:
            print("CUDA is not available with the installed PyTorch. Using CPU mode.")

    # Install other dependencies if needed
    if not is_package_installed("gradio") or not is_package_installed("kokoro"):
        install_dependencies()
    else:
        print("Required dependencies are already installed.")

    # Run the application
    run_app()

if __name__ == "__main__":
    main()
