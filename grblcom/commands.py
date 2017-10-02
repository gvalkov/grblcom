import logging
import shlex
import asyncio
import textwrap
import typing
from pathlib import Path
from optparse import OptionParser, Option

from ansimarkup import ansiprint

log = logging.getLogger()

class CommandError(Exception):
    pass


class Command:
    def __new__(cls):
        cmd_instance = super().__new__(cls)

        options = getattr(cmd_instance, 'options', None)
        if options:
            parser = OptionParser(add_help_option=False, option_list=cls.options)
        else:
            parser = None

        cmd_instance._parser = parser
        return cmd_instance

    def __call__(self, grbl, cli, input_line: str, request_input: typing.Callable):
        if self._parser:
            args = shlex.split(input_line)[1:]
            opts, args = self._parser.parse_args(args)
        else:
            opts, args = None, None

        if self.needs_input and not args:
            extra_input = request_input()
        else:
            extra_input = None
        msg = 'Command "%s" called with arguments "%s" parsed into "%s"'
        log.debug(msg, self.__class__.__name__, args, opts)

        return self.run(grbl, cli, opts, args, extra_input)

    async def run(self, grbl, cli, options, args, extra_input):
        raise NotImplemented


class Run(Command):
    needs_input = True
    options = [
        Option('-m', '--mode', choices=('async', 'sync'), default='sync')
    ]

    def file_contents_iter(self, paths):
        for path in paths:
            with open(path, 'rb') as fh:
                for line in fh:
                    yield line

    async def run(self, cli, opts, args, extra_input):
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
    async def run(self, grbl, cli, opts, args, extra_input):
        await grbl.enable_check()


class Help(Command):
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

