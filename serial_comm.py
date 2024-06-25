import serial
import serial.tools.list_ports
import time

class SerialComm:
    def __init__(self, port, baudrate, bytesize, parity, stopbits, flow_control, terminator):
        self.port = port
        self.baudrate = baudrate
        self.bytesize = bytesize
        self.parity = parity
        self.stopbits = stopbits
        self.flow_control = flow_control
        self.terminator = terminator
        self.ser = None
        self.send_buffer = ""
        self.receive_buffer = ""

    def configure_port(self):
        self.ser = serial.Serial()
        self.ser.port = self.port
        self.ser.baudrate = self.baudrate
        self.ser.bytesize = self.bytesize
        self.ser.parity = self.parity
        self.ser.stopbits = self.stopbits

        if self.flow_control == 'hardware':
            self.ser.rtscts = True
        elif self.flow_control == 'software':
            self.ser.xonxoff = True
        else:
            self.ser.rtscts = False
            self.ser.xonxoff = False

    def open(self):
        if self.ser and not self.ser.is_open:
            self.ser.open()

    def close(self):
        if self.ser and self.ser.is_open:
            self.ser.close()

    def send_data(self):
        if self.ser and self.ser.is_open and self.send_buffer:
            self.ser.write(self.send_buffer.encode() + self.terminator.encode())
            self.send_buffer = "" 

    def receive_data(self, size=1):
        if self.ser and self.ser.is_open:
            self.receive_buffer = self.ser.read(size).decode()
            return self.receive_buffer

    def read_until_terminator(self):
        if self.ser and self.ser.is_open:
            buffer = ''
            while True:
                byte = self.ser.read(1).decode()
                if byte == self.terminator:
                    break
                buffer += byte
            self.receive_buffer = buffer
            return buffer

    def send_binary_data(self, hex_data):
        if self.ser and self.ser.is_open:
            self.ser.write(bytes.fromhex(hex_data))

    def receive_binary_data(self, size=1):
        if self.ser and self.ser.is_open:
            return self.ser.read(size).hex()

    def transaction(self, data, response_size, timeout):
        if self.ser and self.ser.is_open:
            self.ser.timeout = timeout
            self.ser.write(data.encode() + self.terminator.encode())
            return self.ser.read(response_size).decode()

    def ping(self):
        if self.ser and self.ser.is_open:
            self.ser.write(b'PING' + self.terminator.encode())
            start_time = time.time()
            response = self.ser.read(4)
            return time.time() - start_time

    def autobaud(self):
        for baudrate in [300, 600, 1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200]:
            self.ser.baudrate = baudrate
            self.ser.write(b'PING' + self.terminator.encode())
            response = self.ser.read(4)
            if response == b'PONG':
                return baudrate
        return None

    def add_to_send_buffer(self, data):
        self.send_buffer += data

    def get_send_buffer(self):
        return self.send_buffer

    def get_receive_buffer(self):
        return self.receive_buffer

def list_serial_ports():
    return [port.device for port in serial.tools.list_ports.comports()]
