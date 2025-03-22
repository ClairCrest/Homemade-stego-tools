import cv2
import numpy as np
import os
import subprocess
import tempfile
from cryptography.fernet import Fernet
import base64
import re
import zlib  # Added for CRC32 error detection

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
        
        # Calculate video duration in seconds
        duration = total_frames / fps
        
        # Check if video exceeds the duration limit (11 seconds)
        if duration >= 10.7:
            print(f"Error: Video duration is {duration:.2f} seconds.")
            print("Please use a video that is less than 11 seconds long for better steganography results.")
            cap.release()
            return
            
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
        
        # Add a more distinctive termination marker (increased from 24 to 48 bits)
        # This longer pattern makes it much less likely to occur naturally
        termination_marker = '101010101010101010101010010101010101010101010101'
        binary_message += termination_marker
        
        print(f"Message length: {len(secret_data)} characters")
        print(f"Binary length: {len(binary_message)} bits")
        
        # Calculate CRC32 checksum for error detection (32 bits)
        if isinstance(secret_data, str):
            crc = zlib.crc32(secret_data.encode())
        else:
            crc = zlib.crc32(secret_data)
        crc_binary = format(crc, '032b')
        
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
        color_shift = 18  # Increased from 12 to make changes more detectable in longer videos
        
        # Select keyframes for encoding (every 3rd frame to reduce density for longer videos)
        keyframe_interval = 3  # Increased from 2 to spread data more evenly in longer videos
        
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
        
        # Create a redundant header with message length and CRC
        # Format: [16-bit length][32-bit CRC][16-bit length copy]
        header = f"{len(binary_message):016b}{crc_binary}{len(binary_message):016b}"
        
        # Prepend the header to the binary message
        binary_message = header + binary_message
        
        # Record debug info for decoding
        debug_info = {
            "total_bits": len(binary_message),
            "block_size": block_size,
            "keyframe_interval": keyframe_interval,
            "grid_width": encoding_width,
            "grid_height": encoding_height,
            "start_x": start_x,
            "start_y": start_y,
            "color_shift": color_shift
        }
        
        # Report encoding parameters
        print(f"Encoding grid: {encoding_width}x{encoding_height} blocks, {blocks_per_frame} blocks per frame")
        print(f"Color shift: {color_shift}, Keyframe interval: {keyframe_interval}")
        print(f"Header: Length(16 bits) + CRC32(32 bits) + Length copy(16 bits)")
        
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
                        block[:, :, 2] = np.clip(block[:, :, 2].astype(int) + color_shift, 0, 255)  # Red +
                        block[:, :, 0] = np.clip(block[:, :, 0].astype(int) - color_shift, 0, 255)  # Blue -
                    else:
                        # Increase blue, decrease red
                        block[:, :, 0] = np.clip(block[:, :, 0].astype(int) + color_shift, 0, 255)  # Blue +
                        block[:, :, 2] = np.clip(block[:, :, 2].astype(int) - color_shift, 0, 255)  # Red -
                    
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
        """Decode a secret message from a video using the subtle approach.
        
        Args:
            video_path: Path to the video containing hidden data
            key: Fernet decryption key (if None, assumes plaintext)
            
        Returns:
            The extracted message
        """
        # Open the video file
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"Error: Could not open video file {video_path}")
            return "Error: Could not open video file"
            
        # Get video properties
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Define decoding parameters (must match encoding parameters)
        block_size = 16
        
        # Calculate encoding grid dimensions (in the center of the frame)
        encoding_width = (frame_width // 3) // block_size
        encoding_height = (frame_height // 3) // block_size
        blocks_per_frame = encoding_width * encoding_height
        
        # Starting position of encoding grid (centered)
        start_x = (frame_width - (encoding_width * block_size)) // 2
        start_y = (frame_height - (encoding_height * block_size)) // 2
        
        # Select keyframes for decoding (match encoding setting)
        keyframe_interval = 3  # Updated to match encoding
        
        # Increased color threshold for more robust bit detection
        color_threshold = 2  # Increased from 1 for better detection
        
        # Prepare for extraction
        binary_message = ''
        frame_count = 0
        
        # Define termination marker (must match encoding)
        termination_marker = '101010101010101010101010010101010101010101010101'
        
        # First pass: try to get length header and CRC (first 64 bits)
        # [16-bit length][32-bit CRC][16-bit length copy]
        header_bits = ''
        
        print(f"Starting decoding process...")
        print(f"Video properties: {frame_width}x{frame_height}, {total_frames} frames")
        print(f"Decoding grid: {encoding_width}x{encoding_height} blocks, {blocks_per_frame} blocks per frame")
        
        # First pass to get the header
        while cap.isOpened() and len(header_bits) < 64:
            ret, frame = cap.read()
            if not ret:
                break
                
            frame_count += 1
            
            # Only look at keyframes
            if frame_count % keyframe_interval == 0:
                # Examine each block in the encoding grid
                for i in range(min(blocks_per_frame, 64 - len(header_bits))):
                    # Calculate block position in the grid
                    block_x = i % encoding_width
                    block_y = i // encoding_width
                    
                    # Calculate pixel coordinates
                    x = start_x + (block_x * block_size)
                    y = start_y + (block_y * block_size)
                    
                    # Make sure we don't go out of bounds
                    if x+block_size > frame_width or y+block_size > frame_height:
                        continue
                    
                    # Extract the block
                    block = frame[y:y+block_size, x:x+block_size]
                    
                    # Calculate average color values
                    avg_red = np.mean(block[:, :, 2])
                    avg_blue = np.mean(block[:, :, 0])
                    
                    # Decode the bit (if red > blue, bit is 1, otherwise 0)
                    diff = avg_red - avg_blue
                    bit = 1 if diff > color_threshold else 0
                    header_bits += str(bit)
                    
                if len(header_bits) >= 64:
                    break
        
        # Reset video capture
        cap.release()
        cap = cv2.VideoCapture(video_path)
        frame_count = 0
        
        # Parse the header
        length1 = None
        length2 = None
        crc = None
        
        try:
            if len(header_bits) >= 64:
                length1 = int(header_bits[:16], 2)
                crc = int(header_bits[16:48], 2)
                length2 = int(header_bits[48:64], 2)
                
                # Compare the two length values for redundancy
                if length1 == length2:
                    message_length = length1
                    print(f"Detected message length: {message_length} bits (verified)")
                else:
                    # Take the most reasonable value
                    message_length = min(length1, length2)
                    print(f"Length mismatch in header: {length1} vs {length2}, using {message_length}")
            else:
                print(f"Incomplete header: {header_bits}")
                message_length = None  # Fall back to searching for termination marker
        except ValueError:
            print(f"Failed to parse header: {header_bits}")
            message_length = None  # Fall back to searching for termination marker
        
        # Process frames until message_length bits are found or termination marker is found
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
                
            frame_count += 1
            
            # Only look at keyframes
            if frame_count % keyframe_interval == 0:
                # Examine each block in the encoding grid
                for i in range(blocks_per_frame):
                    # Calculate block position in the grid
                    block_x = i % encoding_width
                    block_y = i // encoding_width
                    
                    # Calculate pixel coordinates
                    x = start_x + (block_x * block_size)
                    y = start_y + (block_y * block_size)
                    
                    # Make sure we don't go out of bounds
                    if x+block_size > frame_width or y+block_size > frame_height:
                        continue
                    
                    # Extract the block
                    block = frame[y:y+block_size, x:x+block_size]
                    
                    # Calculate average color values
                    avg_red = np.mean(block[:, :, 2])
                    avg_blue = np.mean(block[:, :, 0])
                    
                    # Decode the bit with improved threshold
                    diff = avg_red - avg_blue
                    bit = 1 if diff > color_threshold else 0
                    binary_message += str(bit)
                    
                    # Debug first few bits
                    if frame_count <= keyframe_interval * 3 and i < 3:
                        print(f"Frame {frame_count}, Bit {len(binary_message)-1}: '{bit}' at ({x},{y}), diff: {diff:.1f}")
                    
                    # Check if we've found enough bits
                    if message_length and len(binary_message) >= message_length + 64:  # +64 for header
                        cap.release()
                        break
                
                # Check if we have enough bits
                if message_length and len(binary_message) >= message_length + 64:
                    break
                    
                # Check for termination marker as fallback
                if not message_length and len(binary_message) >= 100:  # Need at least header + some content
                    # Look for termination marker in the last 100 bits
                    last_bits = binary_message[-100:] if len(binary_message) > 100 else binary_message
                    if termination_marker in last_bits:
                        termination_index = binary_message.rfind(termination_marker)
                        if termination_index != -1:
                            binary_message = binary_message[:termination_index]
                            print(f"Termination marker found at bit {termination_index}")
                            break
                
                # Progress indicator for long videos
                if frame_count % 100 == 0:
                    print(f"Processing frame {frame_count} - extracted {len(binary_message)} bits so far")
                
                # Limit processing to avoid infinite loops
                if frame_count > 4000:  # Increased from 2000 to handle longer videos
                    print(f"Reached frame limit ({frame_count} frames)")
                    break
        
        # Release resources
        cap.release()
        
        # Skip the 64-bit header
        if len(binary_message) >= 64:
            binary_message = binary_message[64:]
        
        # Look for termination marker
        termination_index = binary_message.find(termination_marker)
        if termination_index != -1:
            binary_message = binary_message[:termination_index]
            print(f"Termination marker found after {termination_index} bits")
        
        # Print raw binary data for debugging
        print(f"Raw binary (first 40 bits): {binary_message[:40]}...")
        
        # Convert binary to text
        extracted_message = ''
        for i in range(0, len(binary_message), 8):
            if i+8 <= len(binary_message):
                byte = binary_message[i:i+8]
                try:
                    char_code = int(byte, 2)
                    # Only accept printable ASCII characters and common control chars
                    if 32 <= char_code <= 126 or char_code in [9, 10, 13]:
                        extracted_message += chr(char_code)
                    else:
                        # For debugging: show non-printable characters
                        print(f"Non-printable character at position {i//8}: {byte} = ASCII {char_code}")
                except ValueError:
                    print(f"Invalid byte at position {i}: {byte}")
        
        # Try with inverted bits if nothing sensible was found
        if not extracted_message or not any(32 <= ord(c) <= 126 for c in extracted_message):
            print("No valid characters found. Trying with inverted bits...")
            inverted_binary = ''.join('1' if b == '0' else '0' for b in binary_message)
            inverted_message = ''
            
            for i in range(0, len(inverted_binary), 8):
                if i+8 <= len(inverted_binary):
                    byte = inverted_binary[i:i+8]
                    try:
                        char_code = int(byte, 2)
                        if 32 <= char_code <= 126 or char_code in [9, 10, 13]:
                            inverted_message += chr(char_code)
                    except ValueError:
                        pass
            
            if len(inverted_message) > len(extracted_message):
                extracted_message = inverted_message
                print("Using inverted bit interpretation")
        
        # Try to verify the message using CRC32 if we have it
        if crc is not None and extracted_message:
            try:
                calculated_crc = zlib.crc32(extracted_message.encode())
                if calculated_crc == crc:
                    print(f"CRC32 check passed: message integrity verified")
                else:
                    print(f"CRC32 check failed: {calculated_crc} != {crc}")
                    
                    # Try with minor variations of the message
                    success = False
                    for offset in range(1, 8):
                        # Try skipping a few bits at the start
                        test_binary = binary_message[offset:]
                        test_message = ''
                        for i in range(0, len(test_binary), 8):
                            if i+8 <= len(test_binary):
                                byte = test_binary[i:i+8]
                                try:
                                    char_code = int(byte, 2)
                                    if 32 <= char_code <= 126 or char_code in [9, 10, 13]:
                                        test_message += chr(char_code)
                                except ValueError:
                                    pass
                        
                        calculated_crc = zlib.crc32(test_message.encode())
                        if calculated_crc == crc:
                            extracted_message = test_message
                            print(f"CRC32 check passed with {offset}-bit offset")
                            success = True
                            break
                    
                    if not success:
                        print("Could not verify message integrity through CRC32")
            except Exception as e:
                print(f"CRC32 verification error: {str(e)}")
        
        print(f"Processed {frame_count} frames")
        print(f"Extracted {len(binary_message)} bits")
        print(f"Extracted message (raw): '{extracted_message}'")
        
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
                extracted_message = VideoStego._fix_base64_padding(extracted_message)
                
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
                    for i in range(1, 8):  # Increased range from 4 to 8
                        try:
                            # Try with slightly offset data
                            test_message = extracted_message[i:]
                            test_message = VideoStego._fix_base64_padding(test_message)
                            encrypted_data = base64.b64decode(test_message)
                            decrypted_data = fernet.decrypt(encrypted_data)
                            extracted_message = decrypted_data.decode()
                            print(f"Decryption successful with {i}-character offset")
                            break
                        except Exception:
                            pass
                    
            except Exception as e:
                print(f"Decryption error: {str(e)}. Returning raw extracted data.")
        
        print(f"Final extracted message: '{extracted_message}'")
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