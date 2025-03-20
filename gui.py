import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from stego_tool.image_stego import ImageStego
from stego_tool.audio_stego import AudioStego
from stego_tool.video_stego import VideoStego

class StegoGUI:
    def __init__(self, root):
        self.root = root
        self.root.title('Steganography Tool')
        self.create_widgets()

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

        # Video tab
        self.video_tab = ttk.Frame(tab_control)
        tab_control.add(self.video_tab, text='Video')
        self.create_video_tab()

        tab_control.pack(expand=1, fill='both')

    def create_image_tab(self):
        # Widgets for image encoding and decoding
        ttk.Label(self.image_tab, text='Image Encoding/Decoding').pack()

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
        if input_path and output_path and secret_data:
            ImageStego.encode_image(input_path, secret_data, output_path)
            messagebox.showinfo('Success', f'Data encoded and saved to {output_path}')
            self.clear_image_fields()
        else:
            messagebox.showwarning('Warning', 'Please fill all fields')

    def decode_image(self):
        input_path = self.image_input_path.get()
        if input_path:
            secret_data = ImageStego.decode_image(input_path)
            messagebox.showinfo('Decoded Data', f'Decoded data: {secret_data}')
            self.clear_image_fields()
        else:
            messagebox.showwarning('Warning', 'Please select an input file')

    def clear_image_fields(self):
        self.image_input_path.set('')
        self.image_output_path.set('')
        self.image_secret_data.set('')

    def create_audio_tab(self):
        # Widgets for audio encoding and decoding
        ttk.Label(self.audio_tab, text='Audio Encoding/Decoding').pack()

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
        if input_path and output_path and secret_data:
            AudioStego.encode_audio(input_path, secret_data, output_path)
            messagebox.showinfo('Success', f'Data encoded and saved to {output_path}')
            self.clear_audio_fields()
        else:
            messagebox.showwarning('Warning', 'Please fill all fields')

    def decode_audio(self):
        input_path = self.audio_input_path.get()
        if input_path:
            secret_data = AudioStego.decode_audio(input_path)
            messagebox.showinfo('Decoded Data', f'Decoded data: {secret_data}')
            self.clear_audio_fields()
        else:
            messagebox.showwarning('Warning', 'Please select an input file')

    def clear_audio_fields(self):
        self.audio_input_path.set('')
        self.audio_output_path.set('')
        self.audio_secret_data.set('')

    def create_video_tab(self):
        # Widgets for video encoding and decoding
        ttk.Label(self.video_tab, text='Video Encoding/Decoding').pack()

        # Input file selection
        ttk.Label(self.video_tab, text='Select Input Video:').pack()
        self.video_input_path = tk.StringVar()
        ttk.Entry(self.video_tab, textvariable=self.video_input_path, width=50).pack()
        ttk.Button(self.video_tab, text='Browse', command=self.select_video_input).pack()

        # Output file selection
        ttk.Label(self.video_tab, text='Select Output Video:').pack()
        self.video_output_path = tk.StringVar()
        ttk.Entry(self.video_tab, textvariable=self.video_output_path, width=50).pack()
        ttk.Button(self.video_tab, text='Browse', command=self.select_video_output).pack()

        # Secret message entry
        ttk.Label(self.video_tab, text='Enter Secret Message:').pack()
        self.video_secret_data = tk.StringVar()
        ttk.Entry(self.video_tab, textvariable=self.video_secret_data, width=50).pack()

        # Encode and Decode buttons
        ttk.Button(self.video_tab, text='Encode', command=self.encode_video).pack()
        ttk.Button(self.video_tab, text='Decode', command=self.decode_video).pack()

    def select_video_input(self):
        file_path = filedialog.askopenfilename(filetypes=[('Video Files', '*.mp4;*.avi')])
        if file_path:
            self.video_input_path.set(file_path)

    def select_video_output(self):
        file_path = filedialog.asksaveasfilename(defaultextension='.mp4', filetypes=[('MP4 Files', '*.mp4')])
        if file_path:
            self.video_output_path.set(file_path)

    def encode_video(self):
        input_path = self.video_input_path.get()
        output_path = self.video_output_path.get()
        secret_data = self.video_secret_data.get()
        if input_path and output_path and secret_data:
            VideoStego.encode_video(input_path, secret_data, output_path)
            messagebox.showinfo('Success', f'Data encoded and saved to {output_path}')
            self.clear_video_fields()
        else:
            messagebox.showwarning('Warning', 'Please fill all fields')

    def decode_video(self):
        input_path = self.video_input_path.get()
        if input_path:
            secret_data = VideoStego.decode_video(input_path)
            messagebox.showinfo('Decoded Data', f'Decoded data: {secret_data}')
            self.clear_video_fields()
        else:
            messagebox.showwarning('Warning', 'Please select an input file')

    def clear_video_fields(self):
        self.video_input_path.set('')
        self.video_output_path.set('')
        self.video_secret_data.set('')

if __name__ == '__main__':
    root = tk.Tk()
    app = StegoGUI(root)
    root.mainloop() 