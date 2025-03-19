# stego_tool/video_stego.py
import cv2
import numpy as np

class VideoStego:
    @staticmethod
    def encode_video(video_path, secret_data, output_path):
        cap = cv2.VideoCapture(video_path)
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))
        
        binary_data = ''.join(format(ord(char), '08b') for char in secret_data)
        data_len = len(binary_data)
        
        idx = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            for i in range(frame.shape[0]):
                for j in range(frame.shape[1]):
                    for k in range(3):  # BGR channels
                        if idx < data_len:
                            frame[i, j, k] = frame[i, j, k] & ~1 | int(binary_data[idx])
                            idx += 1
            
            out.write(frame)
        
        cap.release()
        out.release()
        print(f"Data encoded and saved to {output_path}")

    @staticmethod
    def decode_video(video_path):
        cap = cv2.VideoCapture(video_path)
        binary_data = ''
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            for i in range(frame.shape[0]):
                for j in range(frame.shape[1]):
                    for k in range(3):  # BGR channels
                        binary_data += str(frame[i, j, k] & 1)
        
        cap.release()
        
        secret_data = ''
        for i in range(0, len(binary_data), 8):
            byte = binary_data[i:i+8]
            secret_data += chr(int(byte, 2))
            if secret_data[-2:] == '\x00\x00':  # Null terminator
                break
        
        return secret_data[:-2]