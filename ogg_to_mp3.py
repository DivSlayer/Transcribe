import os
from pydub import AudioSegment


def convert_ogg_to_mp3(input_path, output_path=None):
    """Convert an .ogg file to .mp3 format."""
    if not input_path.lower().endswith(".ogg"):
        raise ValueError("Input file must be an .ogg file")

    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"File not found: {input_path}")

    # Load the OGG audio file
    print(f"Loading {input_path}...")
    audio = AudioSegment.from_ogg(input_path)

    # Determine output path
    if output_path is None:
        output_path = os.path.splitext(input_path)[0] + ".mp3"

    # Export as MP3
    print(f"Converting to {output_path}...")
    audio.export(output_path, format="mp3")
    print("Conversion complete!")

convert_ogg_to_mp3('audio.ogg','audio.mp3')