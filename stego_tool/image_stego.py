from PIL import Image
import numpy as np

class ImageStego:
    @staticmethod
    def encode_image(image_path, secret_data, output_path):
        img = Image.open(image_path)
        img = img.convert('RGB')
        pixels = np.array(img, dtype=np.uint8)  # Ensure pixels are uint8
        
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
        
        encoded_img = Image.fromarray(pixels)
        encoded_img.save(output_path)
        print(f"Data encoded and saved to {output_path}")

    @staticmethod
    def decode_image(image_path):
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
                            return ''.join(chr(int(binary_data[n:n+8], 2)) for n in range(0, len(binary_data)-16, 8))
        
        # If no termination marker is found, return all decoded data
        return ''.join(chr(int(binary_data[m:m+8], 2)) for m in range(0, len(binary_data), 8))