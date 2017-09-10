import shlex
from pathlib import Path

from prompt_toolkit.token import Token


class CommandError(Exception):
    pass


def cmd_run(grbl: 'Grbl', input_line: str, token_print):
    paths = shlex.split(input_line)[1:]
    paths = [Path(path) for path in paths]

    for path in paths:
        with path.open('rb') as fh:
            for line in fh:
                lines = grbl.send(line)
                res = [(Token, line.decode('ascii').rstrip())]

                if b'ok' in lines:
                    res.append((Token.Ok, '  ok'))
                else:
                    res.append((Token.Error, '  ' + lines[0].decode('ascii')))
                res.append((Token, '\n'))

                token_print(res)


def cmd_check(grbl: 'Grbl', input_line: str, token_print):
    initial_status = grbl.status()

    try:
        grbl.enable_check()
        cmd_run(grbl, input_line, token_print)
    finally:
        if initial_status[0] != 'Check':
            grbl.disable_check()

