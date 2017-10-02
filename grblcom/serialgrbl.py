import asyncio
import logging

import serial_asyncio

log = logging.getLogger()


class SerialGrbl:
    def __init__(self, device, baudrate, loop):
        self.device = device
        self.baudrate = baudrate
        self.loop = loop

        self.read_queue = asyncio.Queue()
        self.cmd_read_queue = asyncio.Queue()
        self.active_queue = self.read_queue

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

    async def wait_for(self, *responses):
        '''Wait for a series of responses from grbl.'''

        log.debug('Waiting for "%s" from grbl', responses)
        responses_iter = iter(responses)
        response = next(responses_iter, None)

        while True:
            line = await self.cmd_read_queue.get()
            if line == response:
                response = next(responses_iter, None)
                if not response:
                    return True
            else:
                return False

    async def write(self, cmd):
        data = cmd.rstrip() + b'\n'
        log.debug('Serial write: %r', data)
        self.writer.write(data)
        await self.writer.drain()

    async def status(self):
        await self.write(b'?')
        status = await self.cmd_read_queue.get()
        await self.wait_for('ok')
        return status.split()

    async def enable_check(self):
        try:
            self.active_queue = self.cmd_read_queue
            status = await self.status()
            if status[0] != 'Check':
                await self.write(b'$C')
                await self.wait_for('[Enabled]', 'ok')
        finally:
            self.active_queue = self.read_queue

    async def disable_check(self):
        status = self.status()
        if status[0] == 'Check':
            self.write(b'$C')
            self.waitfor(b'[Disabled]', b'ok', timeout=1)

    async def reset(self):
        self.writer.write(b'\x18')  # ctrl+x
        await self.writer.drain()

    async def read_all(self):
        while True:
            line = await self.reader.readline()
            line = line.rstrip().decode('ascii')
            log.debug('Serial read:  %r', line)
            await self.active_queue.put(line)

