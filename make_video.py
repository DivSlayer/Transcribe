import os
import subprocess
import json
import shutil
import tempfile
import locale

def create_video_with_subtitles(audio_path, srt_path, output_path, width=1920, height=1080):
    """
    Create a video with black background, audio, and subtitles using FFmpeg.
    
    Args:
        audio_path (str): Path to the MP3 audio file
        srt_path (str): Path to the SRT subtitle file
        output_path (str): Path where the output video will be saved
        width (int): Video width in pixels
        height (int): Video height in pixels
    """
    # Create temporary directory for working files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create temporary files with ASCII names
        temp_video = os.path.join(temp_dir, 'temp_black.mp4')
        temp_srt = os.path.join(temp_dir, 'temp_subtitles.srt')
        
        # Copy SRT file to temporary location with ASCII name
        shutil.copy2(srt_path, temp_srt)
        
        # Get audio duration using FFmpeg
        duration_cmd = [
            'ffprobe', 
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'json',
            audio_path
        ]
        
        try:
            # Use UTF-8 encoding for FFmpeg output
            result = subprocess.run(duration_cmd, capture_output=True, text=True, encoding='utf-8')
            result.check_returncode()
            duration = float(json.loads(result.stdout)['format']['duration'])
        except Exception as e:
            raise Exception(f"Failed to get audio duration: {str(e)}")
        
        # Create black background video
        try:
            result = subprocess.run([
                'ffmpeg', '-y',
                '-f', 'lavfi',
                '-i', f'color=c=black:s={width}x{height}:d={duration}',
                '-c:v', 'libx264',
                '-preset', 'medium',
                '-crf', '23',
                temp_video
            ], capture_output=True, text=True, encoding='utf-8')
            result.check_returncode()
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to create background video: {e.stderr}")
        
        # Create the final video with audio and subtitles
        try:
            # Escape special characters in the SRT path for FFmpeg
            escaped_srt_path = temp_srt.replace('\\', '\\\\').replace(':', '\\:')
            
            # Use UTF-8 encoding for FFmpeg output
            result = subprocess.run([
                'ffmpeg', '-y',
                '-i', temp_video,
                '-i', audio_path,
                '-vf', f'subtitles={escaped_srt_path}:force_style=\'FontName=Arial,FontSize=24,PrimaryColour=&HFFFFFF,OutlineColour=&H000000,Outline=2,BorderStyle=3,Alignment=2\'',
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-b:a', '192k',
                '-shortest',
                output_path
            ], capture_output=True, text=True, encoding='utf-8')
            result.check_returncode()
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to create final video: {e.stderr}")

if __name__ == '__main__':
    # Example usage
    audio_path = 'output/coverted.mp3'
    srt_path = 'output/coverted_subtitles.srt'
    output_path = 'output_video.mp4'
    
    if os.path.exists(audio_path) and os.path.exists(srt_path):
        create_video_with_subtitles(audio_path, srt_path, output_path)
        print(f"Video created successfully: {output_path}")
    else:
        print("Error: Audio file or subtitle file not found.")