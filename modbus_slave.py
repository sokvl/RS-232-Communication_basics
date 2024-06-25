import asyncio
import threading
from pymodbus.server.async_io import StartAsyncSerialServer as ModbusServer
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.framer.ascii_framer import ModbusAsciiFramer
from pymodbus.framer.rtu_framer import ModbusRtuFramer

class ModbusSlave:
    def __init__(self, port, baudrate, address, method='ascii', timeout=1):
        self.port = port
        self.baudrate = baudrate
        self.address = address
        self.method = method
        self.timeout = timeout
        self.server = None
        self.text_storage = ""
        self.loop = asyncio.new_event_loop()
        self.context = ModbusServerContext(
            slaves={address: ModbusSlaveContext(
                di=ModbusSequentialDataBlock(0, [0]*100),
                co=ModbusSequentialDataBlock(0, [0]*100),
                hr=ModbusSequentialDataBlock(0, [0]*100),
                ir=ModbusSequentialDataBlock(0, [0]*100),
            )},
            single=False
        )

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

    async def handle_request(self, request):
        print(f"Handling request: {request.hex()}")
        try:
            if len(request) < 4:  
                raise ValueError("Received frame too short")

            address = int(request[1:3], 16)
            function_code = int(request[3:5], 16)
            print(f"Parsed address: {address}, function_code: {function_code}")

            if address != self.address:
                print(f"Invalid address: {address} (expected {self.address})")
                return None

            if function_code == 1: # W
                data = request[5:-4]
                self.text_storage = hex_to_text(data.hex())
                response = self.build_response(request[:5])
            elif function_code == 2:  # R
                response_data = text_to_hex(self.text_storage)
                response = self.build_response(request[:5] + bytes.fromhex(response_data))
            else:
                response = self.build_exception_response(request[:5])
            print(f"Sending frame: {response.hex()}")
            return response
        except Exception as e:
            print(f"Error handling request: {e}")
            return self.build_exception_response(request[:5])

    def build_response(self, data):
        if self.method == 'ascii':
            frame = self.build_ascii_frame(self.address, data[1], data[2:])
        else:
            frame = self.build_rtu_frame(self.address, data[1], data[2:])
        return frame

    def build_exception_response(self, data):
        exception_code = 0x01
        if self.method == 'ascii':
            frame = self.build_ascii_frame(self.address, data[1] | 0x80, f"{exception_code:02X}")
        else:
            frame = self.build_rtu_frame(self.address, data[1] | 0x80, f"{exception_code:02X}")
        return frame

    async def start_server(self):
        identity = ModbusDeviceIdentification()
        identity.VendorName = 'Pymodbus'
        identity.ProductCode = 'PM'
        identity.VendorUrl = 'http://github.com/bashwork/pymodbus/'
        identity.ProductName = 'Pymodbus Server'
        identity.ModelName = 'Pymodbus Server'
        identity.MajorMinorRevision = '1.0'

        if self.method == 'ascii':
            await ModbusServer(context=self.context, identity=identity, 
                               framer=ModbusAsciiFramer, port=self.port, 
                               timeout=self.timeout, baudrate=self.baudrate,
                               handle_request=self.handle_request, loop=self.loop)
        else:
            await ModbusServer(context=self.context, identity=identity, 
                               framer=ModbusRtuFramer, port=self.port, 
                               timeout=self.timeout, baudrate=self.baudrate,
                               handle_request=self.handle_request, loop=self.loop)
        
        print(f"Starting Modbus Slave on {self.port} with baudrate {self.baudrate}")

    def start(self):
        self.thread = threading.Thread(target=self.loop.run_until_complete, args=(self.start_server(),))
        self.thread.start()

    def stop(self):
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join()

def text_to_hex(text):
    return text.encode('utf-8').hex()

def hex_to_text(hex_str):
    return bytes.fromhex(hex_str).decode('utf-8')
