import time
import serial


class Grbl:
    gcodes = {
        'G4', 'G10L2', 'G10L20', 'G28', 'G30', 'G28.1', 'G30.1', 'G53', 'G92', 'G92.1',
        'G0', 'G1', 'G2', 'G3', 'G38.2', 'G38.3', 'G38.4', 'G38.5', 'G80',
        'G93', 'G94',
        'G20', 'G21',
        'G90', 'G91',
        'G91.1',
        'G17', 'G18', 'G19',
        'G43.1', 'G49',
        'G40',
        'G54', 'G55', 'G56', 'G57', 'G58', 'G59',
        'G61',
        'M0', 'M1', 'M2', 'M30',
        'M7', 'M8', 'M9',
        'M3', 'M4', 'M5',
        'F,' 'I,' 'J,' 'K,' 'L,' 'N,' 'P,' 'R,' 'S,' 'T,' 'X,' 'Y,' 'Z',
    }

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

    def enable_check(self):
        status = self.status()
        if status[0] != 'Check':
            lines = self.send(b'$C')
            return b'[Enabled]' in lines and b'ok' in lines

    def disable_check(self):
        status = self.status()
        if status[0] == 'Check':
            lines = self.send(b'$C')
            return b'[Disabled]' in lines and b'ok' in lines

    def reset(self):
        self.port.write(24)