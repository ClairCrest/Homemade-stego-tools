from pydub import AudioSegment
import numpy as np
from cryptography.fernet import Fernet
import base64
import re

class AudioStego:
    @staticmethod
    def generate_key():
        """Generate a Fernet encryption key."""
        return Fernet.generate_key()
        
    @staticmethod
    def encode_audio(audio_path, secret_data, output_path, key=None):
        audio = AudioSegment.from_file(audio_path)
        samples = np.array(audio.get_array_of_samples())
        
        # Encrypt the message if a key is provided
        original_data = secret_data
        if key:
            try:
                # Convert string key to bytes if needed
                if isinstance(key, str):
                    key = key.encode()
                
                # Initialize Fernet with the key
                fernet = Fernet(key)
                
                # Encrypt the message
                if isinstance(secret_data, str):
                    secret_data = secret_data.encode()
                encrypted_data = fernet.encrypt(secret_data)
                
                # Convert to base64 string for encoding
                secret_data = base64.b64encode(encrypted_data).decode()
                print(f"Message encrypted using Fernet (length: {len(secret_data)} characters)")
            except Exception as e:
                print(f"Encryption error: {str(e)}. Proceeding with plaintext.")
                secret_data = original_data  # Revert to original data on error
        
        # Add termination marker
        secret_data += '\x00\x00'
        binary_data = ''.join(format(ord(char), '08b') for char in secret_data)
        data_len = len(binary_data)
        
        idx = 0
        for i in range(len(samples)):
            if idx < data_len:
                samples[i] = samples[i] & ~1 | int(binary_data[idx])
                idx += 1
        
        encoded_audio = AudioSegment(
            samples.tobytes(),
            frame_rate=audio.frame_rate,
            sample_width=audio.sample_width,
            channels=audio.channels
        )
        
        # Ensure the output path has a proper extension
        if not output_path.lower().endswith(('.wav', '.mp3', '.ogg', '.flac')):
            # Default to WAV format for lossless encoding
            output_path = output_path + '.wav'
            
        encoded_audio.export(output_path, format="wav")
        print(f"Data encoded and saved to {output_path}")
        print(f"To decode this audio, run: python main.py decode-audio -i {output_path}" + 
              (f" -k \"{key.decode() if isinstance(key, bytes) else key}\"" if key else ""))

    @staticmethod
    def decode_audio(audio_path, key=None):
        audio = AudioSegment.from_file(audio_path)
        samples = np.array(audio.get_array_of_samples())
        
        binary_data = ''
        for sample in samples:
            binary_data += str(sample & 1)
        
        # Extract message until termination marker
        extracted_message = ''
        for i in range(0, len(binary_data), 8):
            if i + 8 <= len(binary_data):
                byte = binary_data[i:i+8]
                char = chr(int(byte, 2))
                extracted_message += char
                if extracted_message[-2:] == '\x00\x00':  # Null terminator
                    extracted_message = extracted_message[:-2]  # Remove termination marker
                    break
                    
        # Try to decrypt the message if a key was provided
        if key and extracted_message:
            try:
                # Convert string key to bytes if needed
                if isinstance(key, str):
                    key = key.encode()
                
                # Initialize Fernet with the key
                fernet = Fernet(key)
                
                # Prepare for base64 decoding
                # Fix padding issues
                extracted_message = AudioStego._fix_base64_padding(extracted_message)
                
                try:
                    # Decode base64 and decrypt
                    encrypted_data = base64.b64decode(extracted_message)
                    decrypted_data = fernet.decrypt(encrypted_data)
                    
                    # Convert to string
                    if isinstance(decrypted_data, bytes):
                        extracted_message = decrypted_data.decode()
                        
                    print(f"Message successfully decrypted using Fernet")
                except Exception as e:
                    print(f"Primary decryption failed: {str(e)}. Trying alternative approaches...")
                    
                    # Try with different sections of the message (in case of alignment issues)
                    for i in range(1, 4):
                        try:
                            # Try with slightly offset data
                            test_message = extracted_message[i:]
                            test_message = AudioStego._fix_base64_padding(test_message)
                            encrypted_data = base64.b64decode(test_message)
                            decrypted_data = fernet.decrypt(encrypted_data)
                            extracted_message = decrypted_data.decode()
                            print(f"Decryption successful with {i}-character offset")
                            break
                        except Exception:
                            pass
                    
            except Exception as e:
                print(f"Decryption error: {str(e)}. Returning raw extracted data.")
        
        return extracted_message
        
    @staticmethod
    def _fix_base64_padding(data):
        """Fix base64 padding issues by ensuring proper length."""
        # Remove non-base64 characters
        data = re.sub(r'[^A-Za-z0-9+/=]', '', data)
        
        # Add padding if needed
        padding_needed = len(data) % 4
        if padding_needed:
            data += '=' * (4 - padding_needed)
            
        return data