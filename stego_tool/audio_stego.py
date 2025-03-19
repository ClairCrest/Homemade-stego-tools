from pydub import AudioSegment
import numpy as np

class AudioStego:
    @staticmethod
    def encode_audio(audio_path, secret_data, output_path):
        audio = AudioSegment.from_file(audio_path)
        samples = np.array(audio.get_array_of_samples())
        
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
        print(f"To decode this audio, run: python main.py decode-audio -i {output_path}")

    @staticmethod
    def decode_audio(audio_path):
        audio = AudioSegment.from_file(audio_path)
        samples = np.array(audio.get_array_of_samples())
        
        binary_data = ''
        for sample in samples:
            binary_data += str(sample & 1)
        
        secret_data = ''
        for i in range(0, len(binary_data), 8):
            byte = binary_data[i:i+8]
            secret_data += chr(int(byte, 2))
            if secret_data[-2:] == '\x00\x00':  # Null terminator
                break
        
        return secret_data[:-2]