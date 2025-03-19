# Steganography Tools

Steganography Tools is a Python project that allows you to hide secret messages in media files, including images, audio, and video. This project provides a command-line interface (CLI) for encoding and decoding messages using various steganography techniques.

## Features
- **Image Steganography**: Encode and decode messages in images using LSB (Least Significant Bit) steganography.
- **Audio Steganography**: Encode and decode messages in audio files using LSB steganography.
- **Video Steganography**: Encode and decode messages in video files using a subtle method that preserves audio. This approach uses keyframes and modifies color channels to hide data, ensuring minimal visual artifacts.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/ClairCrest/Homemade-stego-tools.git
   cd Homemade-stego-tools
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

The CLI provides several commands for encoding and decoding messages in different media types. Below are some examples:

### Image Steganography
- **Encode a message into an image**:
  ```bash
  python main.py encode-image -i picture/original.png -o picture/encoded.png -d "Secret message"
  ```
- **Decode a message from an image**:
  ```bash
  python main.py decode-image -i picture/encoded.png
  ```

### Audio Steganography
- **Encode a message into an audio file**:
  ```bash
  python main.py encode-audio -i audio/original.wav -o audio/encoded.wav -d "Secret message"
  ```
- **Decode a message from an audio file**:
  ```bash
  python main.py decode-audio -i audio/encoded.wav
  ```

### Video Steganography
- **Encode a message into a video**:
  ```bash
  python main.py encode-video -i video/original.mp4 -o video/encoded.mp4 -d "Secret message"
  ```
- **Decode a message from a video**:
  ```bash
  python main.py decode-video -i video/encoded.mp4
  ```

## Modules

- **`image_stego.py`**: Contains the `ImageStego` class for encoding and decoding messages in images.
- **`audio_stego.py`**: Contains the `AudioStego` class for encoding and decoding messages in audio files.
- **`video_stego.py`**: Contains the `VideoStego` class for encoding and decoding messages in video files while preserving audio.
- **`cli.py`**: Provides the command-line interface for interacting with the steganography tools.
- **`utils.py`**: Utility functions for binary conversion.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
