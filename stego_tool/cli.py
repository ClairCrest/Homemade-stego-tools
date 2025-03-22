# stego_tool/cli.py
import click
import os
import cv2
from .image_stego import ImageStego
from .audio_stego import AudioStego
from .video_stego import VideoStego
from cryptography.fernet import Fernet

HELP_TEXT = """
Steganography Tool - Hide secret messages in media files

Examples:
  # Hide a message in an image:
  python main.py encode-image -i picture/original.png -o picture/encoded.png -d "Secret message"

  # Hide an encrypted message in an image:
  python main.py encode-image -i picture/original.png -o picture/encoded.png -d "Secret message" -k "your-encryption-key"

  # Decode a message from an image:
  python main.py decode-image -i picture/encoded.png

  # Decode an encrypted message from an image:
  python main.py decode-image -i picture/encoded.png -k "your-encryption-key"

  # Hide a message in an audio file:
  python main.py encode-audio -i audio/original.wav -o audio/encoded.wav -d "Secret message"

  # Hide an encrypted message in an audio file:
  python main.py encode-audio -i audio/original.wav -o audio/encoded.wav -d "Secret message" -k "your-encryption-key"

  # Decode a message from an audio file:
  python main.py decode-audio -i audio/encoded.wav

  # Decode an encrypted message from an audio file:
  python main.py decode-audio -i audio/encoded.wav -k "your-encryption-key"

  # Generate encryption key:
  python main.py generate-key

  # Hide a message in a video file (with encryption):
  python main.py encode-video -i video/original.mp4 -o video/encoded.mp4 -d "Secret message" -k "your-encryption-key"

  # Decode a message from a video file (with encryption):
  python main.py decode-video -i video/encoded.mp4 -k "your-encryption-key"

  # Hide a message in a video file (without encryption):
  python main.py encode-video -i video/original.mp4 -o video/encoded.mp4 -d "Secret message"

  # Decode a message from a video file (without encryption):
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
@click.option('--key', '-k', help='Encryption key (base64)')
def encode_image(input, output, data, key):
    """Encode a secret message into an image using LSB steganography."""
    ImageStego.encode_image(input, data, output, key)
    
    # Provide appropriate feedback
    if key:
        click.echo(f"Secret encrypted data encoded into {output}")
        click.echo(f"Use the same key with decode-image to retrieve your message")
    else:
        click.echo(f"Secret data encoded into {output}")

@cli.command()
@click.option('--input', '-i', required=True, help='Input image file')
@click.option('--key', '-k', help='Encryption key (base64)')
def decode_image(input, key):
    """Decode a secret message from an image encoded with LSB steganography."""
    secret_data = ImageStego.decode_image(input, key)
    click.echo(f"Decoded data: {secret_data}")

@cli.command()
@click.option('--input', '-i', required=True, help='Input audio file')
@click.option('--output', '-o', required=True, help='Output audio file')
@click.option('--data', '-d', required=True, help='Secret data to encode')
@click.option('--key', '-k', help='Encryption key (base64)')
def encode_audio(input, output, data, key):
    """Encode a secret message into an audio file using LSB steganography."""
    AudioStego.encode_audio(input, data, output, key)
    
    # Provide appropriate feedback
    if key:
        click.echo(f"Secret encrypted data encoded into {output}")
        click.echo(f"Use the same key with decode-audio to retrieve your message")
    else:
        click.echo(f"Secret data encoded into {output}")

@cli.command()
@click.option('--input', '-i', required=True, help='Input audio file')
@click.option('--key', '-k', help='Encryption key (base64)')
def decode_audio(input, key):
    """Decode a secret message from an audio file encoded with LSB steganography."""
    secret_data = AudioStego.decode_audio(input, key)
    click.echo(f"Decoded data: {secret_data}")

@cli.command()
def generate_key():
    """Generate a new Fernet encryption key for steganography."""
    key = Fernet.generate_key()
    key_str = key.decode() if isinstance(key, bytes) else key
    click.echo(f"Generated encryption key: {key_str}")
    click.echo("Keep this key safe! You'll need it to decode your message.")
    return key_str

@cli.command()
@click.option('--input', '-i', required=True, help='Input video file')
@click.option('--output', '-o', required=True, help='Output video file')
@click.option('--data', '-d', required=True, help='Secret data to encode')
@click.option('--file', '-f', is_flag=True, help='Treat data as a file path instead of a string')
@click.option('--key', '-k', help='Encryption key (base64)')
def encode_video(input, output, data, file, key):
    """Encode a message into a video with advanced steganography."""
    # Check video duration
    cap = cv2.VideoCapture(input)
    if not cap.isOpened():
        click.echo(f"Error: Could not open video file {input}")
        return
        
    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Calculate duration in seconds
    duration = frame_count / fps if fps > 0 else 0
    
    # Release the capture object
    cap.release()
    
    # Check if video exceeds 15 seconds
    if duration > 20:
        click.echo(f"Error: Video is too long ({duration:.2f} seconds). Please use a video shorter than 15 seconds.")
        return
    
    # Handle data input
    if file:
        try:
            with open(data, 'rb') as f:
                secret_data = f.read()
        except Exception as e:
            click.echo(f"Error reading file: {e}")
            return
    else:
        secret_data = data
    
    # Call the static method with the key parameter
    VideoStego.encode_video(input, secret_data, output, key)
    
    # Provide appropriate feedback
    if key:
        click.echo(f"Secret encrypted data encoded into {output}")
        click.echo(f"Use the same key with decode-video to retrieve your message")
    else:
        click.echo(f"Secret data encoded into {output}")

@cli.command()
@click.option('--input', '-i', required=True, help='Input video file')
@click.option('--key', '-k', help='Encryption key (base64)')
def decode_video(input, key):
    """Decode a message from a video with advanced steganography."""
    # Call the static method with the key parameter
    secret_data = VideoStego.decode_video(input, key)
    
    click.echo(f"Decoded data: {secret_data}")

if __name__ == '__main__':
    cli()