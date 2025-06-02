import os
import shutil
import subprocess
import sys

def ensure_directories():
    """Ensure all required directories exist."""
    directories = ['templates', 'static', 'uploads', 'chunks']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def clean_build_directories():
    """Clean PyInstaller build directories."""
    dirs_to_clean = ['build', 'dist']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)

def build_executable():
    """Build the executable using PyInstaller."""
    # Ensure all required directories exist
    ensure_directories()
    
    # Clean previous build directories
    clean_build_directories()
    
    # Build the executable
    subprocess.run([
        'pyinstaller',
        '--clean',
        '--noconfirm',
        'transcribe.spec'
    ], check=True)
    
    print("\nBuild completed successfully!")
    print("The executable can be found in the 'dist' directory.")

if __name__ == '__main__':
    try:
        build_executable()
    except subprocess.CalledProcessError as e:
        print(f"Error during build: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1) 