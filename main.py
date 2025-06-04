import subprocess
import os
import speech_recognition as sr
from pydub import AudioSegment
from pydub.utils import make_chunks
from pydub.silence import split_on_silence
import numpy as np


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
        """Handle audio files longer than 1 minute with noise reduction and silence detection"""
        recognizer = sr.Recognizer()
        
        # Adjust silence threshold and minimum silence length
        recognizer.energy_threshold = 300  # Increase threshold to better detect silence
        recognizer.dynamic_energy_threshold = True
        recognizer.pause_threshold = 0.8  # Adjust pause detection threshold
        
        self.chunks = self.split_audio_file()
        start_time = 0  # Track cumulative start time in milliseconds
        total_chunks = len(self.chunks)

        for i, chunk in enumerate(self.chunks):
            chunk_duration = len(chunk)
            end_time = start_time + chunk_duration
            chunk_file = f"chunks/chunk_{i}.wav"

            # Create chunks directory if not exists
            os.makedirs(os.path.dirname(chunk_file), exist_ok=True)

            # Apply noise reduction to the chunk
            chunk = self.reduce_noise(chunk)
            chunk.export(chunk_file, format="wav")

            with sr.AudioFile(chunk_file) as source:
                # Adjust for ambient noise
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
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

    def reduce_noise(self, audio_chunk):
        """Apply gentle noise reduction to an audio chunk"""
        try:
            # Convert to numpy array
            samples = np.array(audio_chunk.get_array_of_samples())
            
            # Normalize the audio
            samples = samples / np.max(np.abs(samples))
            
            # First pass: Gentle noise gate
            noise_gate_threshold = 0.01  # Reduced threshold
            samples = np.where(np.abs(samples) < noise_gate_threshold, samples * 0.5, samples)  # Reduce instead of zeroing
            
            # Second pass: Light spectral noise reduction
            # Convert to frequency domain
            fft_data = np.fft.rfft(samples)
            freqs = np.fft.rfftfreq(len(samples), 1/audio_chunk.frame_rate)
            
            # Apply gentler frequency-based noise reduction
            noise_floor_db = -40  # Less aggressive noise floor
            noise_floor_linear = 10 ** (noise_floor_db / 20)
            
            # Reduce noise in frequency domain more gently
            fft_data[np.abs(fft_data) < noise_floor_linear] *= 0.5  # Reduce by 50% instead of 90%
            
            # Convert back to time domain
            samples = np.fft.irfft(fft_data)
            
            # Third pass: Very gentle dynamic noise reduction
            window_size = 2048  # Larger window for smoother processing
            noise_floor = np.array([
                np.mean(np.abs(samples[i:i+window_size]))
                for i in range(0, len(samples)-window_size, window_size//2)
            ])
            
            # Apply gentler dynamic threshold
            for i in range(0, len(samples)-window_size, window_size//2):
                local_noise_floor = np.mean(noise_floor[max(0, i//(window_size//2)-2):i//(window_size//2)+2])
                threshold = local_noise_floor * 1.5  # Reduced multiplier
                samples[i:i+window_size] = np.where(
                    np.abs(samples[i:i+window_size]) < threshold,
                    samples[i:i+window_size] * 0.7,  # Reduce by 30% instead of 90%
                    samples[i:i+window_size]
                )
            
            # Final pass: Very light smoothing
            window = np.ones(3) / 3  # Smaller window for less smoothing
            samples = np.convolve(samples, window, mode='same')
            
            # Normalize again after processing
            samples = samples / np.max(np.abs(samples))
            
            # Convert back to original scale and ensure values are within int16 range
            max_int16 = np.iinfo(np.int16).max
            min_int16 = np.iinfo(np.int16).min
            samples = samples * max_int16
            samples = np.clip(samples, min_int16, max_int16)
            
            # Convert back to audio segment
            return AudioSegment(
                samples.astype(np.int16).tobytes(),
                frame_rate=audio_chunk.frame_rate,
                sample_width=audio_chunk.sample_width,
                channels=audio_chunk.channels
            )
        except Exception as e:
            print(f"Error in noise reduction: {str(e)}")
            return audio_chunk  # Return original chunk if noise reduction fails

    def split_audio_file(self, chunk_length_ms=59000):  # 59 seconds in milliseconds
        """Try silence-based chunking first, fall back to fixed-length chunks if needed"""
        audio = AudioSegment.from_file(self.audio_path)
        
        # Calculate expected number of chunks for fixed-length approach
        expected_chunks = len(audio) // chunk_length_ms + (1 if len(audio) % chunk_length_ms > 0 else 0)
        
        # Check if we already have the correct number of chunks
        existing_chunks = len([f for f in os.listdir("chunks") if f.startswith("chunk_") and f.endswith(".wav")])
        
        if existing_chunks >= expected_chunks:
            print(f"Found {existing_chunks} existing chunks, reusing them...")
            # Load existing chunks
            chunks = []
            for i in range(existing_chunks):
                chunk_path = f"chunks/chunk_{i}.wav"
                if os.path.exists(chunk_path):
                    chunks.append(AudioSegment.from_wav(chunk_path))
            return chunks
        
        print("Attempting silence-based chunking...")
        # Try silence-based chunking first
        try:
            # More sensitive silence detection parameters
            chunks = split_on_silence(
                audio,
                min_silence_len=300,        # Reduced from 500ms to 300ms
                silence_thresh=audio.dBFS - 10,  # More sensitive threshold
                keep_silence=200,           # Keep less silence at edges
                seek_step=1                 # More precise seeking
            )
            
            # If we got too few chunks, try with even more sensitive parameters
            if len(chunks) < expected_chunks * 0.3:  # If we got less than 30% of expected chunks
                print("First attempt created too few chunks, trying with more sensitive parameters...")
                chunks = split_on_silence(
                    audio,
                    min_silence_len=200,        # Even shorter silence detection
                    silence_thresh=audio.dBFS - 5,  # Even more sensitive threshold
                    keep_silence=100,           # Keep minimal silence
                    seek_step=1                 # More precise seeking
                )
            
            # Verify if we got a reasonable number of chunks
            if len(chunks) >= expected_chunks * 0.3:  # If we got at least 30% of expected chunks
                print(f"Successfully created {len(chunks)} chunks using silence detection")
                # Save chunks to files
                os.makedirs("chunks", exist_ok=True)
                for i, chunk in enumerate(chunks):
                    chunk_path = f"chunks/chunk_{i}.wav"
                    chunk.export(chunk_path, format="wav")
                return chunks
            else:
                print(f"Silence detection created only {len(chunks)} chunks, falling back to fixed-length chunks")
        except Exception as e:
            print(f"Silence detection failed: {str(e)}, falling back to fixed-length chunks")
        
        # Fall back to fixed-length chunks
        print(f"Creating {expected_chunks} fixed-length chunks...")
        os.makedirs("chunks", exist_ok=True)
        chunks = make_chunks(audio, chunk_length_ms)
        
        # Save chunks to files
        for i, chunk in enumerate(chunks):
            chunk_path = f"chunks/chunk_{i}.wav"
            chunk.export(chunk_path, format="wav")
        
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
        pass
     
    def check_folders(self):
        folders = ['chunks','output']
        for folder in folders:
            path = os.path.join(os.getcwd(),folder)
            if not os.path.isdir(path):
                os.makedirs(path,exist_ok=True)
                
    def run(self):
        """Main execution method"""
        self.check_folders()
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

