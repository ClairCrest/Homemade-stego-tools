# Steganography Tools

Steganography Tools is a Python project that allows you to hide secret messages in media files, including images, audio, and video. This project provides both a command-line interface (CLI) and a graphical user interface (GUI) for encoding and decoding messages using various steganography techniques.

## Features
- **Image Steganography**: Encode and decode messages in images using LSB (Least Significant Bit) steganography.
- **Audio Steganography**: Encode and decode messages in audio files using LSB steganography.
- **Video Steganography**: Encode and decode messages in video files using a subtle method that preserves audio. This approach uses keyframes and modifies color channels to hide data, ensuring minimal visual artifacts.
- **Encryption Support**: All steganography methods support Fernet encryption to secure your hidden messages with a key.
- **Error Detection**: Implements CRC32 error detection in video steganography for robust data recovery.

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

3. Make sure ffmpeg is installed on your system (required for video processing).

## Usage

### Graphical User Interface (GUI)
The GUI provides an easy-to-use interface for encoding and decoding messages without using the command line.

1. Run the GUI:
   ```bash
   python gui.py
   ```

2. Use the tabbed interface to select between Image, Audio, and Video steganography.

3. For each tab:
   - Optionally generate or enter an encryption key
   - Select input and output files
   - Enter your secret message
   - Click Encode or Decode as needed

**Important Notes:**
- For video steganography, input videos must be less than 11 seconds long.
- When using encryption, you must use the same key for encoding and decoding.

### Creating an Executable
To create an executable file for the GUI:

1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```

2. Create the executable:
   ```bash
   pyinstaller --onefile --windowed gui.py
   ```

3. Find the executable in the `dist` directory.

### Command-Line Interface (CLI)
The CLI provides several commands for encoding and decoding messages in different media types. Below are some examples:

#### Generate an Encryption Key
```bash
python main.py generate-key
```

#### Image Steganography
- **Encode a message into an image**:
  ```bash
  python main.py encode-image -i picture/original.png -o picture/encoded.png -d "Secret message"
  ```
- **Encode an encrypted message into an image**:
  ```bash
  python main.py encode-image -i picture/original.png -o picture/encoded.png -d "Secret message" -k "your-encryption-key"
  ```
- **Decode a message from an image**:
  ```bash
  python main.py decode-image -i picture/encoded.png
  ```
- **Decode an encrypted message from an image**:
  ```bash
  python main.py decode-image -i picture/encoded.png -k "your-encryption-key"
  ```

#### Audio Steganography
- **Encode a message into an audio file**:
  ```bash
  python main.py encode-audio -i audio/original.wav -o audio/encoded.wav -d "Secret message"
  ```
- **Encode an encrypted message into an audio file**:
  ```bash
  python main.py encode-audio -i audio/original.wav -o audio/encoded.wav -d "Secret message" -k "your-encryption-key"
  ```
- **Decode a message from an audio file**:
  ```bash
  python main.py decode-audio -i audio/encoded.wav
  ```
- **Decode an encrypted message from an audio file**:
  ```bash
  python main.py decode-audio -i audio/encoded.wav -k "your-encryption-key"
  ```

#### Video Steganography
- **Encode a message into a video** (must be less than 11 seconds):
  ```bash
  python main.py encode-video -i video/original.mp4 -o video/encoded.mp4 -d "Secret message"
  ```
- **Encode an encrypted message into a video**:
  ```bash
  python main.py encode-video -i video/original.mp4 -o video/encoded.mp4 -d "Secret message" -k "your-encryption-key"
  ```
- **Decode a message from a video**:
  ```bash
  python main.py decode-video -i video/encoded.mp4
  ```
- **Decode an encrypted message from a video**:
  ```bash
  python main.py decode-video -i video/encoded.mp4 -k "your-encryption-key"
  ```

## Technical Details

### Steganography Methods

#### LSB (Least Significant Bit) for Images and Audio
The tool modifies the least significant bits of pixels (in images) or audio samples to store binary data with minimal perceptual change.

#### Video Steganography Method
Uses a more sophisticated approach:
- Encodes data only in keyframes (every 3rd frame)
- Modifies color channels (red and blue) in 16×16 pixel blocks
- Adds a distinctive termination marker and CRC32 checksum for error detection
- Preserves the original audio track
- Supports videos up to 10.7 seconds in length

### Encryption
- Uses Fernet symmetric encryption (from the cryptography package)
- Provides secure key generation
- Encrypted data is encoded as base64 before being hidden in the media files

## Modules

- **`image_stego.py`**: Contains the `ImageStego` class for encoding and decoding messages in images.
- **`audio_stego.py`**: Contains the `AudioStego` class for encoding and decoding messages in audio files.
- **`video_stego.py`**: Contains the `VideoStego` class for encoding and decoding messages in video files while preserving audio.
- **`cli.py`**: Provides the command-line interface for interacting with the steganography tools.
- **`gui.py`**: Provides the graphical user interface for the steganography tools.

## Requirements

See `requirements.txt` for a complete list of dependencies.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
