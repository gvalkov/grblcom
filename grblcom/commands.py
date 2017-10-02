import logging
import shlex
import asyncio
import argparse
import textwrap
import typing

from ansimarkup import ansiprint

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
        args = None
        if self._parser:
            args = shlex.split(input_line)[1:]
            try:
                opts = self._parser.parse_known_args(args)
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
        Opt('file', type=argparse.FileType(), nargs='?')
    ]

    def file_contents_iter(self, paths):
        for path in paths:
            with open(path, 'rb') as fh:
                for line in fh:
                    yield line

    async def run(self, cli, opts, extra_input):
        if args:
            gcode = self.file_contents_iter(args)
        else:
            gcode = extra_input

        if opts.mode == 'sync':
            return self.run_sync(gcode)
        elif opts.mode == 'async':
            return self.run_async(gcode)

    async def run_sync(self, gcode: list):
        for line in gcode:
            self.write(line)
            await self.grbl.expect('ok')

    async def run_async(self, gcode: list):
        pass


class Check(Run):
    async def run(self, grbl, cli, opts, request_input):
        await grbl.enable_check()


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
