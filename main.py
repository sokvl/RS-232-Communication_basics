from modbus_master import ModbusMaster
from modbus_slave import ModbusSlave
from serial_comm import SerialComm, list_serial_ports

def main():
    ports = list_serial_ports()
    print(f"Available ports: {', '.join(ports)}")
    port = input("Enter the port to use (e.g., COM3 or /dev/ttyUSB0): ")
    baudrate = int(input("Enter baudrate (e.g., 9600): "))
    method = input("Enter method (ascii or rtu): ").lower()

    role = input("Enter role (master, slave, or serial_comm): ").lower()

    if role == 'master':
        timeout = float(input("Enter transaction timeout (0-10 seconds): "))
        retries = int(input("Enter number of retries (0-5): "))
        inter_char_timeout = float(input("Enter inter-character timeout (0-1 seconds): "))

        master = ModbusMaster(port, baudrate, method, timeout, retries, inter_char_timeout)
        master.connect()

        while True:
            command = input("Enter command (send_text, read_text, or exit): ").lower()
            if command == "send_text":
                address = int(input("Enter slave address: "))
                text = input("Enter text to send: ")
                response = master.send_text(address, text)
                print(f"Response: {response}")
            elif command == "read_text":
                address = int(input("Enter slave address: "))
                received_text = master.read_text(address)
                if received_text:
                    print(f"Received text: {received_text}")
                else:
                    print("No response or timeout.")
            elif command == "exit":
                break
            else:
                print("Unknown command.")

        master.close()
    elif role == 'slave':
        address = int(input("Enter slave address (1-247): "))
        timeout = float(input("Enter inter-character timeout (0-1 seconds): "))

        slave = ModbusSlave(port, baudrate, address, method, timeout)
        try:
            slave.start()
            print("Modbus Slave running. Press Ctrl+C to stop.")
            slave.thread.join()
        except KeyboardInterrupt:
            slave.stop()
            print("Modbus Slave stopped.")
    elif role == 'serial_comm':
        bytesize = int(input("Enter bytesize (7 or 8): "))
        parity = input("Enter parity (N, E, O): ").upper()
        stopbits = int(input("Enter stopbits (1 or 2): "))
        flow_control = input("Enter flow control (None, hardware, software): ").lower()
        terminator_choice = input("Enter terminator (None, CR, LF, CR-LF, custom): ").lower()

        if terminator_choice == 'none':
            terminator = ''
        elif terminator_choice == 'cr':
            terminator = '\r'
        elif terminator_choice == 'lf':
            terminator = '\n'
        elif terminator_choice == 'cr-lf':
            terminator = '\r\n'
        else:
            terminator = input("Enter custom terminator (1 or 2 characters): ")

        serial_comm = SerialComm(port, baudrate, bytesize, parity, stopbits, flow_control, terminator)
        serial_comm.configure_port()
        serial_comm.open()

        while True:
            command = input("Enter command (send_text, read_text, send_binary, read_binary, transaction, ping, autobaud, edit_buffer, view_buffer, or exit): ").lower()
            if command == "send_text":
                text = input("Enter text to send: ")
                serial_comm.add_to_send_buffer(text)
                serial_comm.send_data()
                print("Text sent.")
            elif command == "read_text":
                received_text = serial_comm.read_until_terminator()
                print(f"Received text: {received_text}")
            elif command == "send_binary":
                hex_data = input("Enter hex data to send (e.g., '48656c6c6f'): ")
                serial_comm.send_binary_data(hex_data)
                print("Binary data sent.")
            elif command == "read_binary":
                size = int(input("Enter number of bytes to read: "))
                received_binary_data = serial_comm.receive_binary_data(size)
                print(f"Received binary data (hex): {received_binary_data}")
            elif command == "transaction":
                data = input("Enter data to send: ")
                response_size = int(input("Enter expected response size: "))
                timeout = float(input("Enter timeout (seconds): "))
                response = serial_comm.transaction(data, response_size, timeout)
                print(f"Transaction response: {response}")
            elif command == "ping":
                ping_time = serial_comm.ping()
                if ping_time is not None:
                    print(f"Round trip delay: {ping_time:.3f} seconds")
                else:
                    print("PING failed.")
            elif command == "autobaud":
                detected_baudrate = serial_comm.autobaud()
                if detected_baudrate:
                    print(f"Autobauding successful. Detected baudrate: {detected_baudrate}")
                else:
                    print("Autobauding failed.")
            elif command == "edit_buffer":
                text = input("Enter text to add to send buffer: ")
                serial_comm.add_to_send_buffer(text)
                print(f"Current send buffer: {serial_comm.get_send_buffer()}")
            elif command == "view_buffer":
                print(f"Send buffer: {serial_comm.get_send_buffer()}")
                print(f"Receive buffer: {serial_comm.get_receive_buffer()}")
            elif command == "exit":
                break
            else:
                print("Unknown command.")

        serial_comm.close()

if __name__ == "__main__":
    main()
