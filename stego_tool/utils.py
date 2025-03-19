# stego_tool/utils.py
def to_binary(data):
    return ''.join(format(ord(char), '08b') for char in data)

def from_binary(binary_data):
    return ''.join(chr(int(binary_data[i:i+8], 2)) for i in range(0, len(binary_data), 8))