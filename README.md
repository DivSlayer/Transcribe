# Persian Audio Transcriber

A GUI application for transcribing Persian audio files and creating videos with subtitles.

## Prerequisites

1. Install FFmpeg:
   - Windows: Download from https://ffmpeg.org/download.html and add to PATH
   - Linux: `sudo apt-get install ffmpeg`
   - macOS: `brew install ffmpeg`

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Building the Executable

1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```

2. Run the build script:
   ```bash
   python build.py
   ```

3. The executable will be created in the `dist` folder.

## Usage

1. Run the executable
2. Click "Browse" to select an audio file
3. Click "Transcribe" to start transcription
4. Once transcription is complete, click "Create Video" to generate a video with subtitles

## Supported Audio Formats

- MP3
- WAV
- M4A
- OGG (automatically converted to MP3)

## Output Files

- `*_transcript.txt`: Contains the transcribed text
- `*_subtitles.srt`: Contains the subtitles in SRT format
- `*_video.mp4`: The final video with subtitles 