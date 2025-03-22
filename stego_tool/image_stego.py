from PIL import Image
import numpy as np
from cryptography.fernet import Fernet
import base64
import re

class ImageStego:
    @staticmethod
    def generate_key():
        """Generate a Fernet encryption key."""
        return Fernet.generate_key()
        
    @staticmethod
    def encode_image(image_path, secret_data, output_path, key=None):
        img = Image.open(image_path)
        img = img.convert('RGB')
        pixels = np.array(img, dtype=np.uint8)  # Ensure pixels are uint8
        
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
        
        # Add a termination marker to the secret data
        secret_data += '\x00\x00'
        binary_data = ''.join(format(ord(char), '08b') for char in secret_data)
        data_len = len(binary_data)
        
        idx = 0
        for i in range(pixels.shape[0]):
            for j in range(pixels.shape[1]):
                for k in range(3):  # RGB channels
                    if idx < data_len:
                        # Clear the LSB and set it to the binary data bit
                        pixels[i, j, k] = (pixels[i, j, k] & 0xFE) | int(binary_data[idx])
                        idx += 1
                    else:
                        break
                else:
                    continue
                break
            else:
                continue
            break
        
        # Ensure the output path has a proper extension
        if not output_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
            # Default to PNG format for best quality without compression artifacts
            output_path = output_path + '.png'
            
        encoded_img = Image.fromarray(pixels)
        encoded_img.save(output_path)
        print(f"Data encoded and saved to {output_path}")
        print(f"To decode this image, run: python main.py decode-image -i {output_path}" + 
              (f" -k \"{key.decode() if isinstance(key, bytes) else key}\"" if key else ""))

    @staticmethod
    def decode_image(image_path, key=None):
        img = Image.open(image_path)
        img = img.convert('RGB')
        pixels = np.array(img, dtype=np.uint8)
        
        binary_data = ''
        for i in range(pixels.shape[0]):
            for j in range(pixels.shape[1]):
                for k in range(3):  # RGB channels
                    # Extract the LSB
                    binary_data += str(pixels[i, j, k] & 1)
                    # Check for the termination marker every 16 bits (2 bytes)
                    if len(binary_data) >= 16:
                        # Convert the last 16 bits to characters
                        last_chars = ''.join(chr(int(binary_data[m:m+8], 2)) for m in range(len(binary_data)-16, len(binary_data), 8))
                        if last_chars == '\x00\x00':
                            # Remove the termination marker and return the decoded data
                            extracted_message = ''.join(chr(int(binary_data[n:n+8], 2)) for n in range(0, len(binary_data)-16, 8))
                            
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
                                    extracted_message = ImageStego._fix_base64_padding(extracted_message)
                                    
                                    # Decode base64 and decrypt
                                    encrypted_data = base64.b64decode(extracted_message)
                                    decrypted_data = fernet.decrypt(encrypted_data)
                                    
                                    # Convert to string
                                    if isinstance(decrypted_data, bytes):
                                        extracted_message = decrypted_data.decode()
                                        
                                    print(f"Message successfully decrypted using Fernet")
                                except Exception as e:
                                    print(f"Decryption error: {str(e)}. Returning raw extracted data.")
                            
                            return extracted_message
        
        # If no termination marker is found, return all decoded data
        extracted_message = ''.join(chr(int(binary_data[m:m+8], 2)) for m in range(0, len(binary_data), 8))
        
        # Try to decrypt the message if a key was provided
        if key and extracted_message:
            try:
                # Convert string key to bytes if needed
                if isinstance(key, str):
                    key = key.encode()
                
                # Initialize Fernet with the key
                fernet = Fernet(key)
                
                # Prepare for base64 decoding
                extracted_message = ImageStego._fix_base64_padding(extracted_message)
                
                # Decode base64 and decrypt
                encrypted_data = base64.b64decode(extracted_message)
                decrypted_data = fernet.decrypt(encrypted_data)
                
                # Convert to string
                if isinstance(decrypted_data, bytes):
                    extracted_message = decrypted_data.decode()
                    
                print(f"Message successfully decrypted using Fernet")
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