import time
import binascii
from pymodbus.client import ModbusSerialClient as ModbusClient

class ModbusMaster:
    def __init__(self, port, baudrate, method='ascii', timeout=1, retries=3, inter_char_timeout=0.1):
        self.port = port
        self.baudrate = baudrate
        self.method = method
        self.timeout = timeout
        self.retries = retries
        self.inter_char_timeout = inter_char_timeout
        self.client = None

    def connect(self):
        if self.method == 'ascii':
            self.client = ModbusClient(method='ascii', port=self.port, baudrate=self.baudrate, timeout=self.timeout)
        else:
            self.client = ModbusClient(method='rtu', port=self.port, baudrate=self.baudrate, timeout=self.timeout)
        self.client.connect()

    def close(self):
        if self.client:
            self.client.close()

    def build_ascii_frame(self, address, function_code, data):
        lrc = self.calculate_lrc(address, function_code, data)
        frame = f":{address:02X}{function_code:02X}{data}{lrc:02X}\r\n"
        print(f"Built ASCII frame: {frame}")
        return frame.encode()

    def build_rtu_frame(self, address, function_code, data):
        frame = bytes([address, function_code]) + data
        crc = self.calculate_crc(frame)
        frame += crc.to_bytes(2, byteorder='little')
        return frame

    def calculate_lrc(self, address, function_code, data):
        lrc = address + function_code
        lrc += sum(bytes.fromhex(data))
        lrc = ((lrc ^ 0xFF) + 1) & 0xFF
        print(f"Calculated LRC: {lrc:02X}")
        return lrc

    def calculate_crc(self, frame):
        crc = 0xFFFF
        for pos in frame:
            crc ^= pos
            for _ in range(8):
                if (crc & 0x0001) != 0:
                    crc >>= 1
                    crc ^= 0xA001
                else:
                    crc >>= 1
        return crc

    def send_request(self, address, function_code, data):
        for _ in range(self.retries):
            if self.method == 'ascii':
                frame = self.build_ascii_frame(address, function_code, data)
            else:
                frame = self.build_rtu_frame(address, function_code, data)
            print(f"Sending frame: {frame.hex() if isinstance(frame, bytes) else frame}")
            self.client.send(frame)
            start_time = time.time()
            response = self.client.recv(256)
            if response:
                print(f"Received frame: {response.hex()}")
                return response
            if time.time() - start_time > self.timeout:
                continue
        return None

    def send_text(self, address, text):
        hex_data = text_to_hex(text)
        print(f"Sending text as hex: {hex_data}")
        response = self.send_request(address, 1, hex_data)
        return response

    def read_text(self, address):
        response = self.send_request(address, 2, '')
        if response:
            return hex_to_text(response.hex())
        return None

def text_to_hex(text):
    return text.encode('utf-8').hex()

def hex_to_text(hex_str):
    return bytes.fromhex(hex_str).decode('utf-8')
