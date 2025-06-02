import os
import subprocess
import json

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
    # Create a temporary video with black background
    temp_video = 'temp_black.mp4'
    
    # Get audio duration using FFmpeg
    duration_cmd = [
        'ffprobe', 
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'json',
        audio_path
    ]
    
    duration = float(json.loads(subprocess.check_output(duration_cmd).decode())['format']['duration'])
    
    # Create black background video
    subprocess.run([
        'ffmpeg', '-y',
        '-f', 'lavfi',
        '-i', f'color=c=black:s={width}x{height}:d={duration}',
        '-c:v', 'libx264',
        '-preset', 'medium',
        '-crf', '23',
        temp_video
    ], check=True)
    
    # Create the final video with audio and subtitles
    subprocess.run([
        'ffmpeg', '-y',
        '-i', temp_video,
        '-i', audio_path,
        '-vf', f'subtitles={srt_path}:force_style=\'FontName=Arial,FontSize=24,PrimaryColour=&HFFFFFF,OutlineColour=&H000000,Outline=2,BorderStyle=3,Alignment=2\'',
        '-c:v', 'libx264',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-shortest',
        output_path
    ], check=True)
    
    # Clean up temporary file
    if os.path.exists(temp_video):
        os.remove(temp_video)

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