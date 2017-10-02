import asyncio
import typing
import logging

import serial_asyncio

log = logging.getLogger()


class SerialGrbl:
    def __init__(self, device, baudrate, loop):
        self.device = device
        self.baudrate = baudrate
        self.loop = loop

        self.read_lock = asyncio.Lock()
        self.read_queue = asyncio.Queue()

        self.reader = None
        self.writer = None
        self.transport = None

    async def connect(self):
        log.debug('Connecting to "%s" with baudrate "%s"', self.device, self.baudrate)
        serial_kwargs = {'baudrate': self.baudrate, 'url': self.device}
        coro = serial_asyncio.open_serial_connection(loop=self.loop, **serial_kwargs)
        self.reader, self.writer = await coro
        self.transport = self.writer.transport
        return self.reader, self.writer, self.transport

    async def wakeup(self):
        # Wakeup grbl.
        self.writer.write(b'\r\n\r\n')
        await self.writer.drain()

    async def wait_for_prompt(self):
        while True:
            line = await self.reader.readline()
            if line.startswith(b'Grbl'):
                return line.rstrip().decode('ascii')

    async def wait_for(self, data):
        log.debug('Waiting for "%s" from grbl', responses)
        while True:
            line = await self.reader.readline()
            if line == data:
                return True

    async def write(self, cmd):
        self.writer.write(cmd.rstrip() + b'\n')
        log.debug('Serial write: %r', data)
        await self.writer.drain()

    async def status(self):
        self.write(b'?')
        status = await self.reader.readline()
        return status.split()

    async def enable_check(self):
        async with self.read_lock:
            status = await self.status()
            if status[0] != 'Check':
                self.write(b'$C')
                self.wait_for(b'[Enabled]')

    async def disable_check(self):
        status = self.status()
        if status[0] == 'Check':
            self.write(b'$C')
            self.waitfor(b'[Disabled]', b'ok', timeout=1)

    async def reset(self):
        self.writer.write(b'\x18')  # ctrl+x
        await self.writer.drain()

    async def read_all