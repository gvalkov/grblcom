import sys
import asyncio
import logging
import argparse
import textwrap
import functools

import serial
from ansimarkup import ansiprint
from prompt_toolkit import CommandLineInterface
from prompt_toolkit.document import Document
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.key_binding.defaults import load_key_bindings_for_prompt
from prompt_toolkit.keys import Keys
from prompt_toolkit.renderer import print_tokens
from prompt_toolkit.shortcuts import create_prompt_application, create_asyncio_eventloop
from prompt_toolkit.styles import style_from_dict
from prompt_toolkit.token import Token

from grblcom.serialgrbl import SerialGrbl
from . import __version__
from . import commands
from . import utils


logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
log = logging.getLogger()


token_styles = style_from_dict({
    Token.Bold:   'bold',
    Token.Ok:     '#00FF00 bold',
    Token.Error:  '#FF0000 bold',
})


key_to_func = {
    '?':           commands.on_key_question_mark,
    Keys.ControlX: commands.on_key_ctrl_x,
}


cli_commands = {
    '%run': commands.Run(),
    '%check': commands.Check(),
    'help': commands.Help(),
}


def parseargs(args):
    description = '''
    Rich serial-console client for GRBL.
    '''

    epilog = '''
    Example usage:
      grblcom -b 115200 /dev/ttyUSB0
    '''

    parser = argparse.ArgumentParser(
        formatter_class=utils.CompactHelpFormatter,
        description=textwrap.dedent(description),
        epilog=textwrap.dedent(epilog),
        add_help=False
    )

    group = parser.add_argument_group('General options');
    arg = group.add_argument
    arg('-h', '--help', action='help', help='show this help message and exit')
    arg('-d', '--debug', action='store_true', help='show debug messages')
    arg('-v', '--version', action='version', version='grblcom version %s' % __version__)

    group = parser.add_argument_group('Serial port options');
    arg = group.add_argument
    arg('-b', '--baudrate', type=int, help='baud rate (default: 115200)', default=115200)

    group = parser.add_argument_group('Required options')
    arg = group.add_argument
    arg('device', help='path to serial device (e.g. /dev/ttyUSB0)')

    return parser, parser.parse_args(args)


def tprint(*tokens, output, style=token_styles, newline=True):
    if newline:
        tokens = tuple((*tokens, (Token, '\n')))
    print_tokens(output, tokens, style)


async def repl_coro(grbl, cli, commands):
    def is_command(line):
        if line.startswith('%') or line == 'help':
            cmd = line.split()[0]
            return commands.get(cmd)

    async def request_input():
        with cli.patch_stdout_context(raw=True):
            res = await cli.run_async()
            if isinstance(res, Document):
                return res.text
            return res

    while True:
        input_line = await request_input()

        cmd = is_command(input_line)
        if cmd:
            await cmd(grbl, cli, input_line, request_input)
        else:
            await grbl.write(input_line.encode('ascii'))


async def reader_coro(grbl, cli, loop):
    while True:
        line = await grbl.reader.readline()
        line = line.rstrip().decode('ascii')

        # TODO: Using print_tokens/tprint causes strange text output issues
        # TODO: when combined with patch_stdout. We'll just use another
        # TODO: terminal colorization method for now.

        if line == 'ok':
            ansiprint(f'<b><g>{line}</g></b>')
            #tprint((Token.Ok, line), output=cli.output)
        elif line.startswith('Grbl') and line.endswith(']'):
            ansiprint(f'<b>{line}</b>')
        # elif line.startswith('<') and line.endswith('>'):
        #     ansiprint(f'<b>{line}</b>')
        elif line.startswith('error:'):
            msg = line.split(':', 1)[-1]
            ansiprint(f'<b><r>error:</r></b>{msg}')
        else:
            #tprint((Token, line), output=cli.output)
            print(line)

        cli.request_redraw()


async def main_coro(loop, grbl, cli):
    try:
        reader, writer, transport = await grbl.connect()
    except serial.SerialException as error:
        log.fatal(error)
        return 1

    # Wait for grbl prompt.
    prompt_line = await grbl.wait_for_prompt()
    tprint((Token.Bold, prompt_line), output=cli.output)

    tasks = asyncio.gather(
        asyncio.ensure_future(reader_coro(grbl, cli, loop)),
        asyncio.ensure_future(repl_coro(grbl, cli, cli_commands))
    )

    try:
        await tasks
    except (EOFError, KeyboardInterrupt):
        tasks.cancel()
        return 0
    finally:
        tasks.cancel()
        transport.close()


def main(args=sys.argv[1:]):
    parser, args = parseargs(args)

    if args.debug:
        log.setLevel(logging.DEBUG)

    loop = asyncio.get_event_loop()
    grbl = SerialGrbl(args.device, args.baudrate, loop)

    registry = load_key_bindings_for_prompt()
    history = InMemoryHistory()

    app_loop = create_asyncio_eventloop(loop=loop)
    app = create_prompt_application(message='> ', history=history, key_bindings_registry=registry)
    cli = CommandLineInterface(application=app, eventloop=app_loop)

    for key, func in key_to_func.items():
        func = functools.partial(func, grbl=grbl, loop=loop)
        registry.add_binding(key, eager=True)(func)

    try:
        main_task = asyncio.ensure_future(main_coro(loop, grbl, cli))
        return loop.run_until_complete(main_task)
    except (EOFError, KeyboardInterrupt):
        main_task.cancel()
        return 1
    except serial.SerialException as error:
        log.fatal(error)
        return 1


if __name__ == '__main__':
    sys.exit(main())
