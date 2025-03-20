# main.py
from stego_tool.cli import cli
import click

VERSION = "1.0.0"

BANNER = r"""
  ____  _                        _____           _     
 / ___|| |_ ___  __ _  ___      |_   _|__   ___ | |___ 
 \___ \| __/ _ \/ _` |/ _ \ _____| |/ _ \ / _ \| / __|
  ___) | ||  __/ (_| | (_) |_____| | (_) | (_) | \__ \
 |____/ \__\___|\__, |\___/      |_|\___/ \___/|_|___/
                |___/                                  
"""

def display_banner():
    """Display the application banner."""
    click.echo(click.style(BANNER, fg="green"))
    click.echo(click.style(f"Steganography Tools v{VERSION}", fg="cyan", bold=True))
    click.echo(click.style("Hide secret messages in images, audio, and video files\n", fg="white"))

if __name__ == '__main__':
    display_banner()
    cli()