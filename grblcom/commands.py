import logging
import shlex
import asyncio
import argparse
import textwrap
import typing

from ansimarkup import ansiprint

from .serialgrbl import SerialGrbl
from .utils import Signature as Opt, NonFatalArgumentParser

log = logging.getLogger()


class CommandError(Exception):
    pass


class BaseCommand:
    '''
    Base class of all commands.
    '''

    def __new__(cls):
        cmd_instance = super().__new__(cls)

        cmd_instance._parser = None

        # Add an ArgumentParser to every instance that has a 'options' attribute.
        options = getattr(cmd_instance, 'options', None)
        if options:
            parser = NonFatalArgumentParser(usage='', add_help=False)
            for signature in cmd_instance.options:
                parser.add_argument(*signature.args, **signature.kwargs)
            cmd_instance._parser = parser

        return cmd_instance

    async def __call__(self, grbl, cli, input_line: str, request_input: typing.Callable):
        args, opts = None, None
        if self._parser:
            args = shlex.split(input_line)[1:]
            try:
                opts, _ = self._parser.parse_known_args(args)
            except argparse.ArgumentError as error:
                ansiprint(f'<r>error: {error}</r>')
                return

        msg = 'Command "%s" called with arguments "%s" parsed into "%s"'
        log.debug(msg, self.__class__.__name__, args, opts)

        return await self.run(grbl, cli, opts, request_input)

    async def run(self, grbl, cli, opts, request_input):
        raise NotImplemented


class Run(BaseCommand):
    options = [
        Opt('-m', '--mode', choices=('async', 'sync'), default='sync'),
        Opt('files', type=argparse.FileType(), nargs='*')
    ]

    async def run(self, grbl, cli, opts, request_input):
        pass


class Check(BaseCommand):
    options = [
        Opt('-m', '--mode', choices=('async', 'sync'), default='sync'),
        Opt('-c', '--continue-on-error', action='store_true'),
        Opt('files', type=argparse.FileType(), nargs='*')
    ]

    async def run(self, grbl: SerialGrbl, cli, opts, request_input):
        await grbl.enable_check()
        gcode = (line.rstrip() for fh in opts.files for line in fh)
        await self.sync_run(grbl, gcode, not opts.continue_on_error)

    async def sync_run(self, grbl: SerialGrbl, gcode, break_on_error=True):
        with grbl.cmd_queue_ctx():
            for line in gcode:
                await grbl.write(line.encode('ascii'))
                res = await grbl.active_queue.get()
                ansiprint(f'{line} ... ', end='')
                if res == 'ok':
                    ansiprint('<b><g>ok</g></b>')
                else:
                    ansiprint(f'<b><r>{res}</r></b>')
                    if break_on_error:
                        break


class Help(BaseCommand):
    needs_input = False

    async def run(self, grbl, cli, opts, args, extra_input):
        msg = '''
        <b>Grblcom commands:</b>

        <b>%run [-m|--mode=sync,async] [file]</b>
          TODO:

        <b>%check [-m|--mode=sync,async] [file]</b>
          TODO:

        '''
        ansiprint(textwrap.dedent(msg).strip())


def on_key_question_mark(event, grbl, loop):
    asyncio.ensure_future(grbl.write(b'?'), loop=loop)


def on_key_ctrl_x(event, grbl, loop):
    asyncio.ensure_future(grbl.reset(), loop=loop)
