import sys
import logging
import argparse
import textwrap

import serial
from prompt_toolkit.token import Token

from . import utils, repl
from . import commands, grbl as _grbl
from . import __version__


log = logging.getLogger()


token_styles = {
    Token.Ok:     '#00FF00 bold',
    Token.Error:  '#FF0000 bold',
}

commands = {
    '%run': commands.cmd_run,
    '%check': commands.cmd_check,
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


def main(args=sys.argv[1:]):
    parser, args = parseargs(args)

    log.info('connecting to %s' % args.device)
    port = serial.Serial(port=args.device, baudrate=args.baudrate, timeout=0.1)
    grbl = _grbl.Grbl(port, timeout=0.1)

    log.info('waiting for GRBL to initialize')
    grbl.wakeup()

    try:
        repl.repl(grbl, args, token_styles, commands)
    except (EOFError, KeyboardInterrupt):
        port.close()
        return 0


if __name__ == '__main__':
    sys.exit(main())

