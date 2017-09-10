import functools
from prompt_toolkit.contrib.completers import WordCompleter

from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.shortcuts import print_tokens, prompt
from prompt_toolkit.styles import style_from_dict
from prompt_toolkit.token import Token




def parse_response(lines):
    res = []

    for line in lines:
        if line == b'ok':
            res += [
                (Token.Ok, 'ok'),
                (Token, '\n')
            ]
            continue

        if line.startswith(b'error:'):
            msg = line.split(b'error:', 1)[-1].lstrip().decode('ascii')
            res += [
                (Token.Error, 'error: '),
                (Token, msg), (Token, '\n')
            ]
            continue

        res += [
            (Token, line.decode('ascii')),
            (Token, '\n')
        ]

    return res


def is_command(line, commands):
    if line.startswith('%'):
        cmd = line.split()[0]
        return commands.get(cmd)


def repl(grbl: 'Grbl', args, token_styles, commands):
    token_styles = style_from_dict(token_styles)
    token_print = functools.partial(print_tokens, style=token_styles)

    history = InMemoryHistory()
    completer = WordCompleter(grbl.gcodes, ignore_case=True)

    prompt_func = functools.partial(
        prompt, message='> ', history=history, completer=completer,
    )


    while True:
        input_line = prompt_func(display_completions_in_columns=True)

        cmd = is_command(input_line, commands)
        if cmd:
            cmd(grbl, input_line, token_print)
        else:
            input_line = input_line.encode('ascii') + b'\n'
            lines = grbl.send(input_line)

            cli_res = parse_response(lines)
            token_print(cli_res)
