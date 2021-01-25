import shlex
import click
from click.core import Context, Parameter
from click.formatting import HelpFormatter
from click.exceptions import UsageError
import copy
from typing import List

def start_repl() -> None:
    while True:
        user_input = input('> ')
        user_args = shlex.split(user_input)
        try:
            repl(user_args)
        except SystemExit:
            pass

def _parentless(context: Context) -> Context:
    ctx = copy.deepcopy(context)
    ctx.parent = None
    return ctx

class ReplCommand(click.Command):
    def format_usage(self, ctx: Context, formatter: HelpFormatter) -> None:
        return super().format_usage(_parentless(ctx), formatter)

    def get_params(self, ctx: Context) -> List[Parameter]:
        return super().get_params(_parentless(ctx))

class ReplGroup(click.Group):
    def invoke(self, ctx: Context):
        ctx.obj = tuple(ctx.args)
        try:    
            super(ReplGroup, self).invoke(ctx)
        except UsageError as e:
            e.ctx = _parentless(e.ctx)
            e.show()

@click.group(cls=ReplGroup)
def repl():
    pass

@repl.command(cls=ReplCommand)
@click.argument('dir', required=True)
def cd(dir: str) -> None:
    click.echo(dir)

