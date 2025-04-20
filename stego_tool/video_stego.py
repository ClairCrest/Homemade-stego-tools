import cv2
import numpy as np
import os
import subprocess
import tempfile
from cryptography.fernet import Fernet
import base64
import re

class VideoStego:
    """A more subtle video steganography approach that minimizes visual artifacts
    and preserves audio by encoding data only in select areas of specific frames."""
    
    @staticmethod
    def generate_key():
        """Generate a Fernet encryption key."""
        return Fernet.generate_key()
    
    @staticmethod
    def encode_video(video_path, secret_data, output_path, key=None):
        """Encode a secret message into a video with minimal visual artifacts.
        
        Args:
            video_path: Path to the source video
            secret_data: Secret message to encode
            output_path: Path to save the output video
            key: Fernet encryption key (if None, plaintext is used)
        """
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
        
        # Open the video file
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"Error: Could not open video file {video_path}")
            return
            
        # Get video properties
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Create a temporary file for the video without audio
        temp_output_path = tempfile.gettempdir() + os.path.sep + "temp_encoded_video.avi"
        
        # Always use AVI container with XVID codec - most reliable
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter(temp_output_path, fourcc, fps, (frame_width, frame_height))
        
        if not out.isOpened():
            print(f"Error: Could not create output video file {temp_output_path}")
            cap.release()
            return
        
        # Convert the secret message to binary
        binary_message = ''
        for char in secret_data:
            binary_message += format(ord(char), '08b')
        
        # Add a unique marker pattern that's unlikely to occur naturally (24 bits)
        # Using a more distinctive pattern for better detection
        termination_marker = '101010101010101010101010'
        binary_message += termination_marker
        
        print(f"Message length: {len(secret_data)} characters")
        print(f"Binary length: {len(binary_message)} bits")
        
        # Use fewer frames and larger changes for better robustness
        # We'll use a grid of blocks in the center of keyframes
        
        # Define encoding parameters
        block_size = 16  # 16×16 pixel blocks for better robustness
        encoding_margin = 50  # Stay away from frame borders
        
        # Calculate encoding grid dimensions (in the center of the frame)
        encoding_width = (frame_width // 3) // block_size
        encoding_height = (frame_height // 3) // block_size
        blocks_per_frame = encoding_width * encoding_height
        
        # Starting position of encoding grid (centered)
        start_x = (frame_width - (encoding_width * block_size)) // 2
        start_y = (frame_height - (encoding_height * block_size)) // 2
        
        # Increase changes for better robustness in longer videos
        color_shift = 12  # Increased from 8 to make changes more detectable
        
        # Select keyframes for encoding (every 2nd frame)
        keyframe_interval = 2  # Reduced from 3 to store more data across more frames
        
        # Calculate max capacity and distribute data more evenly
        total_keyframes = total_frames // keyframe_interval
        bits_per_keyframe = min(blocks_per_frame, (len(binary_message) + total_keyframes - 1) // total_keyframes)
        
        # Warn if the message is too large
        max_bits = total_keyframes * blocks_per_frame
        if len(binary_message) > max_bits:
            print(f"Warning: Message may be too large. Max capacity: ~{max_bits//8} characters")
        
        # Track our progress
        bit_index = 0
        frame_count = 0
        modified_frames = 0
        
        # Add a header with data length for more reliable decoding
        header = f"{len(binary_message):016b}"  # 16-bit length header
        binary_message = header + binary_message
        
        # Record debug info for decoding
        debug_info = {
            "total_bits": len(binary_message),
            "block_size": block_size,
            "keyframe_interval": keyframe_interval,
            "grid_width": encoding_width,
            "grid_height": encoding_height,
            "start_x": start_x,
            "start_y": start_y
        }
        
        # Report encoding parameters
        print(f"Encoding grid: {encoding_width}x{encoding_height} blocks, {blocks_per_frame} blocks per frame")
        print(f"Color shift: {color_shift}, Keyframe interval: {keyframe_interval}")
        
        # Copy all frames, modifying only keyframes
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
                
            frame_count += 1
            
            # Only encode data in keyframes
            if frame_count % keyframe_interval == 0 and bit_index < len(binary_message):
                modified_frame = frame.copy()
                
                # Encode bits in this frame
                bits_in_this_frame = min(blocks_per_frame, len(binary_message) - bit_index)
                
                for i in range(bits_in_this_frame):
                    # Calculate block position in the grid
                    block_x = i % encoding_width
                    block_y = i // encoding_width
                    
                    # Calculate pixel coordinates
                    x = start_x + (block_x * block_size)
                    y = start_y + (block_y * block_size)
                    
                    # Make sure we don't go out of bounds
                    if x+block_size > frame_width or y+block_size > frame_height:
                        continue
                    
                    # Get the bit to encode
                    bit = int(binary_message[bit_index + i])
                    
                    # Extract the block
                    block = modified_frame[y:y+block_size, x:x+block_size].copy()
                    
                    # Apply a more robust modification:
                    # For bit 1: Increase red, decrease blue
                    # For bit 0: Increase blue, decrease red
                    if bit == 1:
                        # Increase red, decrease blue
                        block[:, :, 2] = np.clip(block[:, :, 2].astype(int) + color_shift, 0, 255)  # Red +12
                        block[:, :, 0] = np.clip(block[:, :, 0].astype(int) - color_shift, 0, 255)  # Blue -12
                    else:
                        # Increase blue, decrease red
                        block[:, :, 0] = np.clip(block[:, :, 0].astype(int) + color_shift, 0, 255)  # Blue +12
                        block[:, :, 2] = np.clip(block[:, :, 2].astype(int) - color_shift, 0, 255)  # Red -12
                    
                    # Place the modified block back
                    modified_frame[y:y+block_size, x:x+block_size] = block
                    
                    # Debug first few bits
                    if modified_frames < 3 and i < 3:
                        print(f"Frame {frame_count}, Bit {bit_index + i}: '{bit}' at position ({x},{y})")
                
                # Update bit index
                bit_index += bits_in_this_frame
                modified_frames += 1
                
                # Write the modified frame
                out.write(modified_frame)
            else:
                # Write unmodified frame
                out.write(frame)
            
            # Check if we've encoded all data
            if bit_index >= len(binary_message):
                # Just copy the rest of the frames
                while cap.isOpened():
                    ret, frame = cap.read()
                    if not ret:
                        break
                    out.write(frame)
                break
                
            # Progress indicator for long videos
            if frame_count % 100 == 0:
                print(f"Processing frame {frame_count}/{total_frames} - {frame_count/total_frames*100:.1f}%")
        
        # Release resources
        cap.release()
        out.release()
        
        # Now use ffmpeg to copy the audio from the original video to our encoded video
        try:
            # Make sure the output has the same extension as input to preserve format
            if not output_path.lower().endswith('.mp4') and not output_path.lower().endswith('.avi'):
                output_path = os.path.splitext(output_path)[0] + os.path.splitext(video_path)[1]
                
            print(f"Copying audio from original video to the encoded video...")
            
            # Construct the ffmpeg command
            # -c:v copy = copy video stream without re-encoding
            # -c:a copy = copy audio stream without re-encoding
            ffmpeg_cmd = [
                'ffmpeg', '-y',               # Force overwrite
                '-i', temp_output_path,       # Input: our encoded video without audio
                '-i', video_path,             # Input: original video with audio
                '-c:v', 'copy',               # Copy video stream
                '-c:a', 'copy',               # Copy audio stream
                '-map', '0:v:0',              # Use video from first input
                '-map', '1:a:0',              # Use audio from second input
                output_path                   # Output file
            ]
            
            # Execute the command
            subprocess.run(ffmpeg_cmd, check=True)
            
            print(f"Successfully merged audio into the output video: {output_path}")
            
            # Remove the temporary file
            os.remove(temp_output_path)
            
        except Exception as e:
            print(f"Warning: Failed to copy audio track: {str(e)}")
            print(f"Fallback: Using the video-only output: {temp_output_path}")
            
            # If we can't use ffmpeg, just rename the temp file to the output path
            if os.path.exists(temp_output_path):
                if os.path.exists(output_path):
                    os.remove(output_path)
                os.rename(temp_output_path, output_path)
        
        # If we encoded all bits, display success message
        if bit_index >= len(binary_message):
            print(f"Data encoded successfully in {modified_frames} frames")
            print(f"Total frames processed: {frame_count}")
            print(f"Total bits encoded: {bit_index}")
            print(f"To decode this video, run: python main.py decode-video -i {output_path}" + 
                 (f" -k \"{key.decode() if isinstance(key, bytes) else key}\"" if key else ""))
        else:
            print(f"Warning: Only encoded {bit_index}/{len(binary_message)} bits")
    
    @staticmethod
    def decode_video(video_path, key=None):
        """Decode a secret message from a video using the subtle approach."""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"Error: Could not open video file {video_path}")
            return "Error: Could not open video file"
            
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        block_size = 16
        encoding_width = (frame_width // 3) // block_size
        encoding_height = (frame_height // 3) // block_size
        blocks_per_frame = encoding_width * encoding_height

        start_x = (frame_width - (encoding_width * block_size)) // 2
        start_y = (frame_height - (encoding_height * block_size)) // 2

        keyframe_interval = 2
        termination_marker = '101010101010101010101010'

        binary_message = ''
        frame_count = 0
        header_bits = ''

        # First pass to get header
        while cap.isOpened() and len(header_bits) < 16:
            ret, frame = cap.read()
            if not ret:
                break
            frame_count += 1
            if frame_count % keyframe_interval == 0:
                for i in range(min(blocks_per_frame, 16 - len(header_bits))):
                    block_x = i % encoding_width
                    block_y = i // encoding_width
                    x = start_x + (block_x * block_size)
                    y = start_y + (block_y * block_size)
                    if x+block_size > frame_width or y+block_size > frame_height:
                        continue
                    block = frame[y:y+block_size, x:x+block_size]
                    median_red = np.median(block[:, :, 2])
                    median_blue = np.median(block[:, :, 0])
                    diff = median_red - median_blue
                    bit = 1 if diff > 5 else 0  # ใช้ threshold สัก 5-10
                    header_bits += str(bit)
                if len(header_bits) >= 16:
                    break

        cap.release()
        cap = cv2.VideoCapture(video_path)
        frame_count = 0
        message_length = None

        try:
            message_length = int(header_bits, 2)
            print(f"Detected message length: {message_length} bits")
        except ValueError:
            message_length = None

        # Extract the main message
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            frame_count += 1
            if frame_count % keyframe_interval == 0:
                for i in range(blocks_per_frame):
                    block_x = i % encoding_width
                    block_y = i // encoding_width
                    x = start_x + (block_x * block_size)
                    y = start_y + (block_y * block_size)
                    if x+block_size > frame_width or y+block_size > frame_height:
                        continue
                    block = frame[y:y+block_size, x:x+block_size]
                    median_red = np.median(block[:, :, 2])
                    median_blue = np.median(block[:, :, 0])
                    diff = median_red - median_blue
                    bit = 1 if diff > 0 else 0
                    binary_message += str(bit)
                    # Debug output omitted for brevity
                if message_length and len(binary_message) >= message_length:
                    break
                # Check for termination marker
                if termination_marker in binary_message:
                    termination_index = binary_message.rfind(termination_marker)
                    binary_message = binary_message[:termination_index]
                    break

        cap.release()
        if len(binary_message) >= 16:
            binary_message = binary_message[16:]

        termination_index = binary_message.find(termination_marker)
        if termination_index != -1:
            binary_message = binary_message[:termination_index]
            print(f"Termination marker found after {termination_index} bits")

        # Convert binary to bytes
        extracted_bytes = bytearray()
        for i in range(0, len(binary_message), 8):
            if i+8 > len(binary_message):
                break
            byte_str = binary_message[i:i+8]
            try:
                byte_val = int(byte_str, 2)
                extracted_bytes.append(byte_val)
            except ValueError:
                print(f"Invalid byte at position {i}: {byte_str}")

        extracted_message = extracted_bytes.decode('latin-1', errors='replace')
        extracted_message = VideoStego._fix_base64_padding(extracted_message)

        # Decryption logic remains the same
        if key and extracted_message:
            try:
                fernet = Fernet(key.encode() if isinstance(key, str) else key)
                encrypted_data = base64.b64decode(extracted_message)
                decrypted_data = fernet.decrypt(encrypted_data)
                extracted_message = decrypted_data.decode()
            except Exception as e:
                print(f"Decryption error: {str(e)}. Returning raw data.")

        print(f"Final extracted message: '{extracted_message}'")
        return extracted_message

    @staticmethod
    def _fix_base64_padding(data):
        data = re.sub(r'[^A-Za-z0-9+/=]', '', data)
        padding_needed = len(data) % 4
        if padding_needed:
            data += '=' * (4 - padding_needed)
        return data
