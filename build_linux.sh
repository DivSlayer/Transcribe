#!/bin/bash

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python3 is not installed. Please install Python3 first."
    exit 1
fi

# Install required system packages
echo "Installing required system packages..."
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv ffmpeg

# Create and activate virtual environment
echo "Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install required Python packages
echo "Installing required Python packages..."
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

# Clean previous build directories
echo "Cleaning previous build directories..."
rm -rf build dist

# Create required directories
echo "Creating required directories..."
mkdir -p templates static uploads chunks

# Build the executable
echo "Building executable with PyInstaller..."
pyinstaller --clean --noconfirm transcribe.spec

# Check if build was successful
if [ $? -eq 0 ]; then
    echo "Build completed successfully!"
    echo "The executable can be found in the 'dist' directory."
    # Make the executable executable
    chmod +x dist/transcribe
else
    echo "Build failed!"
    exit 1
fi

# Deactivate virtual environment
deactivate 