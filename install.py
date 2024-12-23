#!/usr/bin/env python3
import subprocess
import sys
import os
from pathlib import Path

def check_uv_installed():
    """Check if uv is installed on the system."""
    try:
        subprocess.run(['uv', '--version'], capture_output=True)
        return True
    except FileNotFoundError:
        return False

def install_uv():
    """Install uv if not already installed."""
    print("Installing uv package manager...")
    try:
        curl_command = "curl -LsSf https://astral.sh/uv/install.sh | sh"
        subprocess.run(curl_command, shell=True, check=True)
        print("uv installed successfully!")
    except subprocess.CalledProcessError:
        print("Failed to install uv. Please install it manually from https://github.com/astral/uv")
        sys.exit(1)

def setup_virtual_environment():
    """Create and activate a virtual environment using uv."""
    print("Setting up virtual environment...")
    subprocess.run(['uv', 'venv'], check=True)

def install_requirements():
    """Install project requirements using uv."""
    if os.path.exists('requirements.txt'):
        print("Installing requirements...")
        subprocess.run(['uv', 'pip', 'install', '-r', 'requirements.txt'], check=True)
    else:
        print("No requirements.txt found. Creating one with basic game dependencies...")
        basic_requirements = [
            'pygame',
            'numpy',
            'python-dotenv',
        ]
        
        with open('requirements.txt', 'w') as f:
            for req in basic_requirements:
                f.write(f"{req}\n")
        
        print("Installing basic requirements...")
        subprocess.run(['uv', 'pip', 'install', '-r', 'requirements.txt'], check=True)

def main():
    print("Starting game installation...")
    
    if not check_uv_installed():
        print("uv is not installed.")
        install_uv()
    
    setup_virtual_environment()
    install_requirements()
    
    print("\nInstallation completed successfully!")
    print("\nTo start the game:")
    print("1. Activate the virtual environment:")
    print("   - On Windows: .venv\\Scripts\\activate")
    print("   - On Unix/MacOS: source .venv/bin/activate")
    print("2. Run the game: python game.py")

if __name__ == "__main__":
    main() 