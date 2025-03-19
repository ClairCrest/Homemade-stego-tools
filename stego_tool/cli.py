# stego_tool/cli.py
import click
from .image_stego import ImageStego
from .audio_stego import AudioStego
from .video_stego import VideoStego

HELP_TEXT = """
Steganography Tool - Hide secret messages in media files

Examples:
  # Hide a message in an image:
  python main.py encode-image -i picture/original.png -o picture/encoded.png -d "Secret message"

  # Decode a message from an image:
  python main.py decode-image -i picture/encoded.png

  # Hide a message in an audio file:
  python main.py encode-audio -i audio/original.wav -o audio/encoded.wav -d "Secret message"

  # Decode a message from an audio file:
  python main.py decode-audio -i audio/encoded.wav

  # Hide a message in a video (standard method):
  python main.py encode-video -i video/original.mp4 -o video/encoded.mp4 -d "Secret message"

  # Decode a message from a video:
  python main.py decode-video -i video/encoded.mp4

"""

@click.group(help=HELP_TEXT)
def cli():
    """Steganography Tool - Hide secret messages in media files (images, audio, video)."""
    pass

@cli.command()
@click.option('--input', '-i', required=True, help='Input image file')
@click.option('--output', '-o', required=True, help='Output image file')
@click.option('--data', '-d', required=True, help='Secret data to encode')
def encode_image(input, output, data):
    """Encode a secret message into an image using LSB steganography."""
    ImageStego.encode_image(input, data, output)

@cli.command()
@click.option('--input', '-i', required=True, help='Input image file')
def decode_image(input):
    """Decode a secret message from an image encoded with LSB steganography."""
    secret_data = ImageStego.decode_image(input)
    click.echo(f"Decoded data: {secret_data}")

@cli.command()
@click.option('--input', '-i', required=True, help='Input audio file')
@click.option('--output', '-o', required=True, help='Output audio file')
@click.option('--data', '-d', required=True, help='Secret data to encode')
def encode_audio(input, output, data):
    """Encode a secret message into an audio file using LSB steganography."""
    AudioStego.encode_audio(input, data, output)

@cli.command()
@click.option('--input', '-i', required=True, help='Input audio file')
def decode_audio(input):
    """Decode a secret message from an audio file encoded with LSB steganography."""
    secret_data = AudioStego.decode_audio(input)
    click.echo(f"Decoded data: {secret_data}")

@cli.command()
@click.option('--input', '-i', required=True, help='Input video file')
@click.option('--output', '-o', required=True, help='Output video file')
@click.option('--data', '-d', required=True, help='Secret data to encode')
def encode_video(input, output, data):
    """Encode a message into a video while preserving audio using ffmpeg."""
    VideoStego.encode_video(input, data, output)

@cli.command()
@click.option('--input', '-i', required=True, help='Input video file')
def decode_video(input):
    """Decode a message from a video encoded with the standard method."""
    secret_data = VideoStego.decode_video(input)
    click.echo(f"Decoded data: {secret_data}") 

if __name__ == '__main__':
    cli()