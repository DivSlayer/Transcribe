import subprocess
import os
import speech_recognition as sr
from pydub import AudioSegment
from pydub.utils import make_chunks
from pydub.silence import split_on_silence


def _ms_to_srt_time(ms):
    """Convert milliseconds to SRT time format"""
    seconds, ms = divmod(ms, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{ms:03d}"


class Transcribe:
    def __init__(self, audio_path, text_path="transcript.txt", srt_path="subtitles.srt", progress_callback=None):
        self.output_folder = "output"
        self.audio_path = audio_path
        self.text_path = os.path.join(os.getcwd(),self.output_folder,text_path)
        self.srt_path = os.path.join(os.getcwd(),self.output_folder,srt_path)
        self.chunks = []
        self.subtitles = []  # Stores timing and text for SRT
        self.progress_callback = progress_callback

    def transcribe_persian_audio(self):
        """Main transcription function with duration handling"""
        audio = AudioSegment.from_file(self.audio_path)
        duration_seconds = len(audio) / 1000

        if duration_seconds > 60:
            print("File too long, splitting into chunks...")
            self.transcribe_long_audio()
        else:
            recognizer = sr.Recognizer()
            with sr.AudioFile(self.audio_path) as source:
                audio_data = recognizer.record(source)
                text = recognizer.recognize_google(
                    audio_data, language='fa-IR')
                self.subtitles.append({
                    'start': 0,
                    'end': len(audio),
                    'text': text
                })
                if self.progress_callback:
                    self.progress_callback(100)

    def transcribe_long_audio(self):
        """Handle audio files longer than 1 minute"""
        recognizer = sr.Recognizer()
        self.chunks = self.split_audio_file()
        start_time = 0  # Track cumulative start time in milliseconds
        total_chunks = len(self.chunks)

        for i, chunk in enumerate(self.chunks):
            chunk_duration = len(chunk)
            end_time = start_time + chunk_duration
            chunk_file = f"chunks/chunk_{i}.wav"

            # Create chunks directory if not exists
            os.makedirs(os.path.dirname(chunk_file), exist_ok=True)

            chunk.export(chunk_file, format="wav")

            with sr.AudioFile(chunk_file) as source:
                audio_data = recognizer.record(source)
                try:
                    text = recognizer.recognize_google(
                        audio_data, language='fa-IR')
                    self.subtitles.append({
                        'start': start_time,
                        'end': end_time,
                        'text': text
                    })
                except Exception as e:
                    print(f"[Error in chunk {i}: {str(e)}]")
                    self.subtitles.append({
                        'start': start_time,
                        'end': end_time,
                        'text': f"[Unable to transcribe chunk {i}]"
                    })

            start_time = end_time  # Update for next chunk
            
            # Calculate and report progress
            if self.progress_callback:
                progress = int((i + 1) / total_chunks * 100)
                self.progress_callback(progress)

    def split_audio_file(self, chunk_length_ms=30000):
        """Split audio based on silence instead of fixed time"""
        audio = AudioSegment.from_file(self.audio_path)

        # Parameters: tweak for your audio
        chunks = split_on_silence(
            audio,
            # Minimum length of silence to be a split point (ms)
            min_silence_len=500,
            # Silence threshold (adjust if too sensitive)
            silence_thresh=audio.dBFS - 16,
            keep_silence=300          # Keep a bit of silence at the edges
        )
        return chunks

    def generate_srt(self):
        """Generate SRT subtitle file from transcribed segments"""
        with open(self.srt_path, 'w', encoding='utf-8') as srt_file:
            for idx, subtitle in enumerate(self.subtitles, 1):
                start = _ms_to_srt_time(subtitle['start'])
                end = _ms_to_srt_time(subtitle['end'])
                text = subtitle['text'].strip()

                srt_entry = (
                    f"{idx}\n"
                    f"{start} --> {end}\n"
                    f"{text}\n\n"
                )
                srt_file.write(srt_entry)

    def cleanup(self):
        """Clean up temporary chunk files"""
        for i in range(len(self.chunks)):
            file_path = f"chunks/chunk_{i}.wav"
            if os.path.isfile(file_path):
                os.remove(file_path)
        if os.path.exists("chunks") and not os.listdir("chunks"):
            os.rmdir("chunks")

    def run(self):
        """Main execution method"""
        self.transcribe_persian_audio()

        # Save raw text transcript
        with open(self.text_path, 'w', encoding='utf-8') as txt_file:
            for segment in self.subtitles:
                txt_file.write(segment['text'] + '\n')
        self.save_transcript_to_txt()
        # Generate SRT subtitles
        self.generate_srt()
        self.cleanup()
        print(f"Transcription complete! Text saved to {self.text_path}")
        print(f"Subtitles saved to {self.srt_path}")

    def save_transcript_to_txt(self):
        """Save all transcribed text to a .txt file"""
        with open(self.text_path, 'w', encoding='utf-8') as txt_file:
            for segment in self.subtitles:
                txt_file.write(segment['text'] + '\n')

