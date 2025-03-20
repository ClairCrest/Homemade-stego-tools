import cv2
import numpy as np
import os
import subprocess
import tempfile

class VideoStego:
    """A more subtle video steganography approach that minimizes visual artifacts
    and preserves audio by encoding data only in select areas of specific frames."""
    
    @staticmethod
    def encode_video(video_path, secret_data, output_path):
        """Encode a secret message into a video with minimal visual artifacts."""
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
        
        # Add a unique marker pattern that's unlikely to occur naturally (16 bits)
        # Using alternating 1s and 0s as termination marker
        termination_marker = '1010101010101010'
        binary_message += termination_marker
        
        print(f"Message: '{secret_data}'")
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
        
        # Select keyframes for encoding (every 5th frame)
        keyframe_interval = 5
        
        # Warn if the message is too large
        max_bits = (total_frames // keyframe_interval) * blocks_per_frame
        if len(binary_message) > max_bits:
            print(f"Warning: Message may be too large. Max capacity: ~{max_bits//8} characters")
        
        # Track our progress
        bit_index = 0
        frame_count = 0
        modified_frames = 0
        
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
                        block[:, :, 2] = np.clip(block[:, :, 2].astype(int) + 5, 0, 255)  # Red +5
                        block[:, :, 0] = np.clip(block[:, :, 0].astype(int) - 5, 0, 255)  # Blue -5
                    else:
                        # Increase blue, decrease red
                        block[:, :, 0] = np.clip(block[:, :, 0].astype(int) + 5, 0, 255)  # Blue +5
                        block[:, :, 2] = np.clip(block[:, :, 2].astype(int) - 5, 0, 255)  # Red -5
                    
                    # Place the modified block back
                    modified_frame[y:y+block_size, x:x+block_size] = block
                    
                    # Debug first few bits
                    if i < 3 and modified_frames < 3:
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
            print(f"To decode this video, run: python main.py decode-video -i {output_path}")
        else:
            print(f"Warning: Only encoded {bit_index}/{len(binary_message)} bits")
    
    @staticmethod
    def decode_video(video_path):
        """Decode a secret message from a video using the subtle approach."""
        # Open the video file
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"Error: Could not open video file {video_path}")
            return "Error: Could not open video file"
            
        # Get video properties
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Define decoding parameters (must match encoding parameters)
        block_size = 16
        
        # Calculate encoding grid dimensions (in the center of the frame)
        encoding_width = (frame_width // 3) // block_size
        encoding_height = (frame_height // 3) // block_size
        blocks_per_frame = encoding_width * encoding_height
        
        # Starting position of encoding grid (centered)
        start_x = (frame_width - (encoding_width * block_size)) // 2
        start_y = (frame_height - (encoding_height * block_size)) // 2
        
        # Select keyframes for decoding (every 5th frame)
        keyframe_interval = 5
        
        # Prepare for extraction
        binary_message = ''
        frame_count = 0
        
        # Define termination marker
        termination_marker = '1010101010101010'
        
        # Process frames until termination marker is found
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
                    
                    # Decode the bit (if red > blue, bit is 1, otherwise 0)
                    bit = 1 if avg_red > avg_blue else 0
                    binary_message += str(bit)
                    
                    # Debug first few bits
                    if frame_count <= keyframe_interval * 3 and i < 3:
                        diff = avg_red - avg_blue
                        print(f"Frame {frame_count}, Bit {len(binary_message)-1}: '{bit}' at ({x},{y}), diff: {diff:.1f}")
                    
                    # Check for termination marker every 16 bits
                    if len(binary_message) >= 16 and binary_message[-16:] == termination_marker:
                        # Found termination marker, remove it and stop
                        binary_message = binary_message[:-16]
                        print(f"Termination marker found after {len(binary_message)} bits")
                        cap.release()
                        break
                
                # Check if termination marker was found
                if len(binary_message) >= 16 and binary_message[-16:] == termination_marker:
                    break
                
                # Limit processing to a reasonable number of frames
                if frame_count > 500:
                    print(f"Reached frame limit ({frame_count} frames)")
                    break
        
        # Release resources
        cap.release()
        
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
        if not any(32 <= ord(c) <= 126 for c in extracted_message):
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
        
        print(f"Processed {frame_count} frames")
        print(f"Extracted {len(binary_message)} bits")
        print(f"Extracted message: '{extracted_message}'")
        return extracted_message 