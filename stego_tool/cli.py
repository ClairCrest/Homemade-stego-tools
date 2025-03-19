# stego_tool/cli.py
import click
from .image_stego import ImageStego
from .audio_stego import AudioStego
from .video_stego import VideoStego

@click.group()
def cli():
    pass

@cli.command()
@click.option('--input', '-i', required=True, help='Input image file')
@click.option('--output', '-o', required=True, help='Output image file')
@click.option('--data', '-d', required=True, help='Secret data to encode')
def encode_image(input, output, data):
    ImageStego.encode_image(input, data, output)

@cli.command()
@click.option('--input', '-i', required=True, help='Input image file')
def decode_image(input):
    secret_data = ImageStego.decode_image(input)
    click.echo(f"Decoded data: {secret_data}")

@cli.command()
@click.option('--input', '-i', required=True, help='Input audio file')
@click.option('--output', '-o', required=True, help='Output audio file')
@click.option('--data', '-d', required=True, help='Secret data to encode')
def encode_audio(input, output, data):
    AudioStego.encode_audio(input, data, output)

@cli.command()
@click.option('--input', '-i', required=True, help='Input audio file')
def decode_audio(input):
    secret_data = AudioStego.decode_audio(input)
    click.echo(f"Decoded data: {secret_data}")

@cli.command()
@click.option('--input', '-i', required=True, help='Input video file')
@click.option('--output', '-o', required=True, help='Output video file')
@click.option('--data', '-d', required=True, help='Secret data to encode')
def encode_video(input, output, data):
    VideoStego.encode_video(input, data, output)

@cli.command()
@click.option('--input', '-i', required=True, help='Input video file')
def decode_video(input):
    secret_data = VideoStego.decode_video(input)
    click.echo(f"Decoded data: {secret_data}")

if __name__ == '__main__':
    cli()