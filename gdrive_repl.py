import shlex
import click
from click.core import Context

def start_repl() -> None:
    while True:
        user_input = input('> ')
        user_args = shlex.split(user_input)
        try:
            repl(user_args)
        except SystemExit:
            pass

class MyGroup(click.Group):
    def invoke(self, ctx):
        ctx.obj = tuple(ctx.args)
        super(MyGroup, self).invoke(ctx)

@click.group(cls=MyGroup)
@click.pass_context
def repl(group_ctx: Context):
    pass

@repl.command()
@click.argument('dir', required=True)
def cd(dir: str) -> None:
    click.echo(dir)

if __name__ == "__main__":
    start_repl()