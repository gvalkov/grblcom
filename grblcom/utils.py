import argparse


class CompactHelpFormatter(argparse.RawTextHelpFormatter):
    def __init__(self, *args, **kw):
        super().__init__(*args, max_help_position=35, **kw)

    def _format_usage(self, *args, **kw):
        usage = super()._format_usage(*args, **kw)
        return usage.capitalize()

    def _format_action_invocation(self, action):
        if not action.option_strings:
            metavar = self._metavar_formatter(action, action.dest)(1)
            return '<%s>' % metavar[0]
        else:
            res = ', '.join(action.option_strings)
            args_string = self._format_args(action, action.dest.upper())
            res = '%s %s' % (res, args_string)
            return res