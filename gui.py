import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from stego_tool.image_stego import ImageStego
from stego_tool.audio_stego import AudioStego
from stego_tool.video_stego import VideoStego
from cryptography.fernet import Fernet
import logging
import cv2
import base64

class StegoGUI:
    def __init__(self, root):
        self.root = root
        self.root.title('Steganography Tool')
        self.create_widgets()
        self.setup_logging()
        self.encryption_key = None

    def setup_logging(self):
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=logging.INFO
        )
        
    def validate_fernet_key(self, key):
        """Validate that the provided key is a valid Fernet key"""
        if not key:
            return False
            
        try:
            # Check if it's base64 decodable
            if len(key) < 32:
                return False
                
            # Try initializing a Fernet object with the key
            Fernet(key.encode())
            return True
        except Exception:
            return False

    def create_widgets(self):
        # Create a tabbed interface
        tab_control = ttk.Notebook(self.root)

        # Image tab
        self.image_tab = ttk.Frame(tab_control)
        tab_control.add(self.image_tab, text='Image')
        self.create_image_tab()

        # Audio tab
        self.audio_tab = ttk.Frame(tab_control)
        tab_control.add(self.audio_tab, text='Audio')
        self.create_audio_tab()

        # # Video tab
        # self.video_tab = ttk.Frame(tab_control)
        # tab_control.add(self.video_tab, text='Video')
        # self.create_video_tab()

        tab_control.pack(expand=1, fill='both')

    def create_image_tab(self):
        # Widgets for image encoding and decoding
        ttk.Label(self.image_tab, text='Image Encoding/Decoding').pack()

        # Encryption Section
        ttk.Label(self.image_tab, text='Encryption Key:').pack()
        self.image_key_var = tk.StringVar()
        self.image_key_var.trace("w", lambda name, index, mode, sv=self.image_key_var: self.on_key_change(sv, "image"))
        ttk.Entry(self.image_tab, textvariable=self.image_key_var, width=50).pack()
        ttk.Button(self.image_tab, text='Generate Key', command=self.generate_image_key).pack()
        self.image_key_status = ttk.Label(self.image_tab, text="")
        self.image_key_status.pack()

        # Input file selection
        ttk.Label(self.image_tab, text='Select Input Image:').pack()
        self.image_input_path = tk.StringVar()
        ttk.Entry(self.image_tab, textvariable=self.image_input_path, width=50).pack()
        ttk.Button(self.image_tab, text='Browse', command=self.select_image_input).pack()

        # Output file selection
        ttk.Label(self.image_tab, text='Select Output Image:').pack()
        self.image_output_path = tk.StringVar()
        ttk.Entry(self.image_tab, textvariable=self.image_output_path, width=50).pack()
        ttk.Button(self.image_tab, text='Browse', command=self.select_image_output).pack()

        # Secret message entry
        ttk.Label(self.image_tab, text='Enter Secret Message:').pack()
        self.image_secret_data = tk.StringVar()
        ttk.Entry(self.image_tab, textvariable=self.image_secret_data, width=50).pack()

        # Encode and Decode buttons
        ttk.Button(self.image_tab, text='Encode', command=self.encode_image).pack()
        ttk.Button(self.image_tab, text='Decode', command=self.decode_image).pack()

    def on_key_change(self, string_var, tab_name):
        """Validates the key whenever it changes"""
        key = string_var.get()
        is_valid = self.validate_fernet_key(key)
        
        if tab_name == "image":
            status_label = self.image_key_status
        elif tab_name == "audio":
            status_label = self.audio_key_status
        else:  # video
            status_label = self.video_key_status
            
        if not key:
            status_label.config(text="")
        elif is_valid:
            status_label.config(text="✓ Valid Fernet key", foreground="green")
        else:
            status_label.config(text="✗ Invalid Fernet key", foreground="red")

    def generate_image_key(self):
        try:
            key = ImageStego.generate_key().decode()
            self.image_key_var.set(key)
            messagebox.showinfo("Success", "New encryption key generated and set!")
        except Exception as e:
            messagebox.showerror("Error", f"Key generation failed: {str(e)}")

    def select_image_input(self):
        file_path = filedialog.askopenfilename(filetypes=[('Image Files', '*.png;*.jpg;*.jpeg;*.bmp;*.tiff')])
        if file_path:
            self.image_input_path.set(file_path)

    def select_image_output(self):
        file_path = filedialog.asksaveasfilename(defaultextension='.png', filetypes=[('PNG Files', '*.png')])
        if file_path:
            self.image_output_path.set(file_path)

    def encode_image(self):
        input_path = self.image_input_path.get()
        output_path = self.image_output_path.get()
        secret_data = self.image_secret_data.get()
        key = self.image_key_var.get() if self.image_key_var.get() else None
        
        # Validate key if provided
        if key and not self.validate_fernet_key(key):
            messagebox.showerror('Error', 'Please enter a valid Fernet encryption key')
            return
        
        if input_path and output_path and secret_data:
            try:
                ImageStego.encode_image(input_path, secret_data, output_path, key)
                messagebox.showinfo('Success', f'Data encoded and saved to {output_path}')
                self.clear_image_fields()
            except Exception as e:
                logging.error("Image encoding failed: %s", str(e))
                messagebox.showerror('Error', f'Encoding failed: {str(e)}')
        else:
            messagebox.showwarning('Warning', 'Please fill all fields')

    def decode_image(self):
        input_path = self.image_input_path.get()
        key = self.image_key_var.get() if self.image_key_var.get() else None
        
        # Validate key if provided
        if key and not self.validate_fernet_key(key):
            messagebox.showerror('Error', 'Please enter a valid Fernet encryption key')
            return
            
        if input_path:
            try:
                secret_data = ImageStego.decode_image(input_path, key)
                messagebox.showinfo('Decoded Data', f'Decoded data: {secret_data}')
                self.clear_image_fields()
            except Exception as e:
                logging.error("Image decoding failed: %s", str(e))
                messagebox.showerror('Error', f'Decoding failed: {str(e)}')
        else:
            messagebox.showwarning('Warning', 'Please select an input file')

    def clear_image_fields(self):
        self.image_input_path.set('')
        self.image_output_path.set('')
        self.image_secret_data.set('')
        # Don't clear the key

    def create_audio_tab(self):
        # Widgets for audio encoding and decoding
        ttk.Label(self.audio_tab, text='Audio Encoding/Decoding').pack()

        # Encryption Section
        ttk.Label(self.audio_tab, text='Encryption Key:').pack()
        self.audio_key_var = tk.StringVar()
        self.audio_key_var.trace("w", lambda name, index, mode, sv=self.audio_key_var: self.on_key_change(sv, "audio"))
        ttk.Entry(self.audio_tab, textvariable=self.audio_key_var, width=50).pack()
        ttk.Button(self.audio_tab, text='Generate Key', command=self.generate_audio_key).pack()
        self.audio_key_status = ttk.Label(self.audio_tab, text="")
        self.audio_key_status.pack()

        # Input file selection
        ttk.Label(self.audio_tab, text='Select Input Audio:').pack()
        self.audio_input_path = tk.StringVar()
        ttk.Entry(self.audio_tab, textvariable=self.audio_input_path, width=50).pack()
        ttk.Button(self.audio_tab, text='Browse', command=self.select_audio_input).pack()

        # Output file selection
        ttk.Label(self.audio_tab, text='Select Output Audio:').pack()
        self.audio_output_path = tk.StringVar()
        ttk.Entry(self.audio_tab, textvariable=self.audio_output_path, width=50).pack()
        ttk.Button(self.audio_tab, text='Browse', command=self.select_audio_output).pack()

        # Secret message entry
        ttk.Label(self.audio_tab, text='Enter Secret Message:').pack()
        self.audio_secret_data = tk.StringVar()
        ttk.Entry(self.audio_tab, textvariable=self.audio_secret_data, width=50).pack()

        # Encode and Decode buttons
        ttk.Button(self.audio_tab, text='Encode', command=self.encode_audio).pack()
        ttk.Button(self.audio_tab, text='Decode', command=self.decode_audio).pack()

    def generate_audio_key(self):
        try:
            key = AudioStego.generate_key().decode()
            self.audio_key_var.set(key)
            messagebox.showinfo("Success", "New encryption key generated and set!")
        except Exception as e:
            messagebox.showerror("Error", f"Key generation failed: {str(e)}")

    def select_audio_input(self):
        file_path = filedialog.askopenfilename(filetypes=[('Audio Files', '*.wav;*.mp3;*.ogg;*.flac')])
        if file_path:
            self.audio_input_path.set(file_path)

    def select_audio_output(self):
        file_path = filedialog.asksaveasfilename(defaultextension='.wav', filetypes=[('WAV Files', '*.wav')])
        if file_path:
            self.audio_output_path.set(file_path)

    def encode_audio(self):
        input_path = self.audio_input_path.get()
        output_path = self.audio_output_path.get()
        secret_data = self.audio_secret_data.get()
        key = self.audio_key_var.get() if self.audio_key_var.get() else None
        
        # Validate key if provided
        if key and not self.validate_fernet_key(key):
            messagebox.showerror('Error', 'Please enter a valid Fernet encryption key')
            return
        
        if input_path and output_path and secret_data:
            try:
                AudioStego.encode_audio(input_path, secret_data, output_path, key)
                messagebox.showinfo('Success', f'Data encoded and saved to {output_path}')
                self.clear_audio_fields()
            except Exception as e:
                logging.error("Audio encoding failed: %s", str(e))
                messagebox.showerror('Error', f'Encoding failed: {str(e)}')
        else:
            messagebox.showwarning('Warning', 'Please fill all fields')

    def decode_audio(self):
        input_path = self.audio_input_path.get()
        key = self.audio_key_var.get() if self.audio_key_var.get() else None
        
        # Validate key if provided
        if key and not self.validate_fernet_key(key):
            messagebox.showerror('Error', 'Please enter a valid Fernet encryption key')
            return
            
        if input_path:
            try:
                secret_data = AudioStego.decode_audio(input_path, key)
                messagebox.showinfo('Decoded Data', f'Decoded data: {secret_data}')
                self.clear_audio_fields()
            except Exception as e:
                logging.error("Audio decoding failed: %s", str(e))
                messagebox.showerror('Error', f'Decoding failed: {str(e)}')
        else:
            messagebox.showwarning('Warning', 'Please select an input file')

    def clear_audio_fields(self):
        self.audio_input_path.set('')
        self.audio_output_path.set('')
        self.audio_secret_data.set('')
        # Don't clear the key

    # def create_video_tab(self):
    #     ttk.Label(self.video_tab, text='Video Encoding/Decoding').pack()
        
    #     # Encryption Section
    #     ttk.Label(self.video_tab, text='Encryption Key:').pack()
    #     self.video_key_var = tk.StringVar()
    #     self.video_key_var.trace("w", lambda name, index, mode, sv=self.video_key_var: self.on_key_change(sv, "video"))
    #     ttk.Entry(self.video_tab, textvariable=self.video_key_var, width=50).pack()
    #     ttk.Button(self.video_tab, text='Generate Key', command=self.generate_video_key).pack()
    #     self.video_key_status = ttk.Label(self.video_tab, text="")
    #     self.video_key_status.pack()

    #     # Input file selection
    #     ttk.Label(self.video_tab, text='Select Input Video:').pack()
    #     self.video_input_path = tk.StringVar()
    #     ttk.Entry(self.video_tab, textvariable=self.video_input_path, width=50).pack()
    #     ttk.Button(self.video_tab, text='Browse', command=self.select_video_input).pack()

    #     # Output file selection
    #     ttk.Label(self.video_tab, text='Select Output Video:').pack()
    #     self.video_output_path = tk.StringVar()
    #     ttk.Entry(self.video_tab, textvariable=self.video_output_path, width=50).pack()
    #     ttk.Button(self.video_tab, text='Browse', command=self.select_video_output).pack()

    #     # Secret message entry
    #     ttk.Label(self.video_tab, text='Enter Secret Message:').pack()
    #     self.video_secret_data = tk.StringVar()
    #     ttk.Entry(self.video_tab, textvariable=self.video_secret_data, width=50).pack()

    #     # Encode and Decode buttons
    #     ttk.Button(self.video_tab, text='Encode', command=self.encode_video).pack()
    #     ttk.Button(self.video_tab, text='Decode', command=self.decode_video).pack()

    # def select_video_input(self):
    #     file_path = filedialog.askopenfilename(filetypes=[('Video Files', '*.mp4;*.avi')])
    #     if file_path:
    #         self.video_input_path.set(file_path)

    # def select_video_output(self):
    #     file_path = filedialog.asksaveasfilename(defaultextension='.mp4', filetypes=[('MP4 Files', '*.mp4')])
    #     if file_path:
    #         self.video_output_path.set(file_path)

    # def generate_video_key(self):
    #     try:
    #         key = VideoStego.generate_key().decode()
    #         self.video_key_var.set(key)
    #         messagebox.showinfo("Success", "New encryption key generated and set!")
    #     except Exception as e:
    #         messagebox.showerror("Error", f"Key generation failed: {str(e)}")

    # def check_video_duration(self, video_path):
    #     try:
    #         cap = cv2.VideoCapture(video_path)
    #         if not cap.isOpened():
    #             messagebox.showerror('Error', f"Could not open video file {video_path}")
    #             return False
                
    #         # Get video properties
    #         fps = cap.get(cv2.CAP_PROP_FPS)
    #         frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
    #         # Calculate duration in seconds
    #         duration = frame_count / fps if fps > 0 else 0
            
    #         # Release the capture object
    #         cap.release()
            
    #         # Check if video exceeds 11 seconds
    #         if duration >= 10.7:
    #             messagebox.showerror('Error', 
    #                                  f"Video is too long ({duration:.2f} seconds). " +
    #                                  "Please use a video shorter than 11 seconds.")
    #             return False
                
    #         return True
    #     except Exception as e:
    #         messagebox.showerror('Error', f"Error checking video duration: {str(e)}")
    #         return False

    # def encode_video(self):
    #     input_path = self.video_input_path.get()
    #     output_path = self.video_output_path.get()
    #     secret_data = self.video_secret_data.get()
    #     key = self.video_key_var.get() if self.video_key_var.get() else None
        
    #     # Validate key if provided
    #     if key and not self.validate_fernet_key(key):
    #         messagebox.showerror('Error', 'Please enter a valid Fernet encryption key')
    #         return
            
    #     if not all([input_path, output_path, secret_data]):
    #         messagebox.showwarning('Warning', 'Please fill all required fields')
    #         return
            
    #     # Check video duration before encoding
    #     if not self.check_video_duration(input_path):
    #         return

    #     try:
    #         # Use the static method directly
    #         VideoStego.encode_video(input_path, secret_data, output_path, key)
            
    #         messagebox.showinfo('Success', f'Data encoded and saved to {output_path}')
    #         self.clear_video_fields()
            
    #     except Exception as e:
    #         logging.error("Encoding failed: %s", str(e))
    #         messagebox.showerror('Error', f'Encoding failed: {str(e)}')

    # def decode_video(self):
    #     input_path = self.video_input_path.get()
    #     key = self.video_key_var.get() if self.video_key_var.get() else None
        
    #     # Validate key if provided
    #     if key and not self.validate_fernet_key(key):
    #         messagebox.showerror('Error', 'Please enter a valid Fernet encryption key')
    #         return
            
    #     if not input_path:
    #         messagebox.showwarning('Warning', 'Please select an input file')
    #         return

    #     try:
    #         # Use the static method directly
    #         secret_data = VideoStego.decode_video(input_path, key)
            
    #         if secret_data:
    #             messagebox.showinfo('Decoded Data', f'Decoded data: {secret_data}')
    #         else:
    #             messagebox.showinfo('Decoded Data', 'No hidden message found or decryption failed')
                
    #         self.clear_video_fields()
            
    #     except Exception as e:
    #         logging.error("Decoding failed: %s", str(e))
    #         messagebox.showerror('Error', f'Decoding failed: {str(e)}')

    # def clear_video_fields(self):
    #     self.video_input_path.set('')
    #     self.video_output_path.set('')
    #     self.video_secret_data.set('')
    #     # Don't clear the encryption key

if __name__ == '__main__':
    root = tk.Tk()
    app = StegoGUI(root)
    root.mainloop() 