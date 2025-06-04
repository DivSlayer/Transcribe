import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading
from main import Transcribe
from make_video import create_video_with_subtitles
from pydub import AudioSegment
import queue

class TranscriptionGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Persian Audio Transcription")
        self.root.geometry("600x400")

        # Variables
        self.audio_path = tk.StringVar()
        self.text_path = tk.StringVar()
        self.srt_path = tk.StringVar()
        self.video_path = tk.StringVar()
        
        # Queue for thread-safe communication
        self.queue = queue.Queue()
        
        # Create main frame
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # File selection
        ttk.Label(main_frame, text="Audio File:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.audio_path, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(main_frame, text="Browse", command=self.browse_audio).grid(row=0, column=2)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, length=400, mode='determinate', variable=self.progress_var)
        self.progress_bar.grid(row=1, column=0, columnspan=3, pady=20)
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="Ready")
        self.status_label.grid(row=2, column=0, columnspan=3, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=3, pady=20)
        
        self.transcribe_button = ttk.Button(button_frame, text="Transcribe", command=self.start_transcription, state='disabled')
        self.transcribe_button.pack(side=tk.LEFT, padx=5)
        
        self.video_button = ttk.Button(button_frame, text="Create Video", command=self.create_video, state='disabled')
        self.video_button.pack(side=tk.LEFT, padx=5)
        
        # Start checking the queue
        self.check_queue()

    def check_queue(self):
        """Check the queue for messages from worker threads"""
        try:
            while True:
                message = self.queue.get_nowait()
                if message['type'] == 'progress':
                    self.progress_var.set(message['value'])
                elif message['type'] == 'status':
                    self.status_label.config(text=message['text'])
                elif message['type'] == 'error':
                    messagebox.showerror("Error", message['text'])
                    self.enable_buttons()
                elif message['type'] == 'success':
                    messagebox.showinfo("Success", message['text'])
                    if message.get('enable_video', False):
                        self.video_button.config(state='normal')
                    else:
                        self.enable_buttons()
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.check_queue)

    def enable_buttons(self):
        """Enable both buttons"""
        self.transcribe_button.config(state='normal')
        self.video_button.config(state='normal')

    def disable_buttons(self):
        """Disable both buttons"""
        self.transcribe_button.config(state='disabled')
        self.video_button.config(state='disabled')

    def convert_ogg_to_mp3(self, input_path):
        """Convert OGG file to MP3 format"""
        try:
            self.queue.put({'type': 'status', 'text': "Converting OGG to MP3..."})

            input_name= '.'.join(input_path.split('.')[:-1])
            input_name = input_name.split('/')[-1]
            output_path = os.path.join(os.getcwd(),'output')
            if not os.path.isdir(output_path):
                os.makedirs(output_path,exist_ok=True)
            output_path = os.path.join(output_path,f"c_{input_name}.mp3")
            audio = AudioSegment.from_ogg(input_path)
            audio.export(output_path, format="mp3")
            
            self.queue.put({'type': 'status', 'text': "OGG to MP3 conversion complete!"})
            return output_path
        except Exception as e:
            raise Exception(f"Failed to convert OGG to MP3: {str(e)}")
        
    def update_progress(self, value):
        """Thread-safe progress update"""
        self.queue.put({'type': 'progress', 'value': value})
        
    def browse_audio(self):
        filename = filedialog.askopenfilename(
            filetypes=[("Audio Files", "*.mp3 *.wav *.m4a *.ogg")]
        )
        if filename:
            # If OGG file is selected, convert it to MP3
            if filename.lower().endswith('.ogg'):
                try:
                    filename = self.convert_ogg_to_mp3(filename)
                except Exception as e:
                    messagebox.showerror("Error", str(e))
                    return
            
            self.audio_path.set(filename)
            # Set default output paths
            base_path = os.path.splitext(filename)[0]
            self.text_path.set(f"{base_path}_transcript.txt")
            self.srt_path.set(f"{base_path}_subtitles.srt")
            self.video_path.set(f"{base_path}_video.mp4")
            # Enable transcribe button after selecting audio
            self.transcribe_button.config(state='normal')

    def transcription_worker(self):
        """Worker thread for transcription"""
        try:
            self.queue.put({'type': 'status', 'text': "Transcribing..."})
            self.queue.put({'type': 'progress', 'value': 0})
            
            transcriber = Transcribe(
                self.audio_path.get(),
                self.text_path.get(),
                self.srt_path.get(),
                progress_callback=self.update_progress
            )
            transcriber.run()
            
            self.queue.put({'type': 'status', 'text': "Transcription completed!"})
            self.queue.put({'type': 'success', 'text': "Transcription completed successfully!", 'enable_video': True})
            
        except Exception as e:
            self.queue.put({'type': 'status', 'text': "Error occurred!"})
            self.queue.put({'type': 'error', 'text': f"An error occurred: {str(e)}"})
            
    def video_worker(self):
        """Worker thread for video creation"""
        try:
            self.queue.put({'type': 'status', 'text': "Creating video..."})
            self.queue.put({'type': 'progress', 'value': 0})
            
            create_video_with_subtitles(
                audio_path=self.audio_path.get(),
                srt_path=self.srt_path.get(),
                output_path=self.video_path.get()
            )
            
            self.queue.put({'type': 'status', 'text': "Video created!"})
            self.queue.put({'type': 'success', 'text': "Video created successfully!"})
            
        except Exception as e:
            self.queue.put({'type': 'status', 'text': "Error occurred!"})
            self.queue.put({'type': 'error', 'text': f"An error occurred: {str(e)}"})
            
    def start_transcription(self):
        if not self.audio_path.get():
            messagebox.showerror("Error", "Please select an audio file first!")
            return
            
        self.disable_buttons()
        # Start transcription in a separate thread
        threading.Thread(target=self.transcription_worker, daemon=True).start()
            
    def create_video(self):
        if not all([self.audio_path.get(), self.srt_path.get(), self.video_path.get()]):
            messagebox.showerror("Error", "Please transcribe the audio first!")
            return
            
        self.disable_buttons()
        # Start video creation in a separate thread
        threading.Thread(target=self.video_worker, daemon=True).start()

def main():
    root = tk.Tk()
    app = TranscriptionGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 