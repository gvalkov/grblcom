import time
import serial


class Grbl:
    def __init__(self, port: serial.Serial, timeout: float):
        self.port = port
        self.timeout = timeout

    def wakeup(self):
        self.port.write(b'\r\n\r\n')
        time.sleep(1.0)
        self.port.flushInput()

    def send(self, cmd):
        cmd = cmd.rstrip() + b'\n'

        self.port.write(cmd)
        lines = self.port.readlines()
        lines = [line.rstrip() for line in lines]
        return lines

    def status(self):
        lines = self.send(b'?')
        return lines[0][1:-1].decode('ascii').split(',')

    def reset(self):
        self.port.write(24)