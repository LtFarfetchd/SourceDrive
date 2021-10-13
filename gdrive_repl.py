import shlex
from typing import Dict, Any, Tuple
import click
from click.core import Context
from click.formatting import HelpFormatter
from click.exceptions import UsageError
import copy
import fs.tree
from fs.base import FS
from fs.tempfs import TempFS
from fs.subfs import SubFS
from gdrive_utils import (
    dir_dive, 
    dir_enumerate, 
    generate_init_data, 
    generate_init_resources
)
from utils import get_input, get_sub_dir_path


root_dir: TempFS
previous_dir: SubFS[FS]
current_dir: SubFS[FS]


class ReplExitSignal(Exception):
    pass


class ReplFinishSignal(Exception):
    pass


class ReplCommand(click.Command):
    def format_usage(self, ctx: Context, formatter: HelpFormatter) -> None:
        return super().format_usage(_parentless(ctx), formatter)


class ReplGroup(click.Group):
    def invoke(self, ctx: Context):
        ctx.obj = tuple(ctx.args)
        try:    
            super(ReplGroup, self).invoke(ctx)
        except UsageError as e:
            e.ctx = _parentless(e.ctx)
            e.show()


def _parentless(context: Context) -> Context:
    ctx = copy.deepcopy(context)
    ctx.parent = None
    return ctx


def run_repl() -> Tuple[str, Dict[str, Dict[str, Any]]]:
    global root_dir, current_dir, previous_dir
    root_dir, current_dir, previous_dir = generate_init_resources()

    while True:
        user_input = get_input()
        user_args = shlex.split(user_input)
        before_dir = current_dir

        try:
            repl(user_args)
        except SystemExit:
            pass
        except ReplExitSignal:
            return ''
        except ReplFinishSignal:
            break
        
        if before_dir != current_dir:
            previous_dir = before_dir

    chosen_dir_path = get_sub_dir_path(current_dir)
    return (chosen_dir_path, generate_init_data(chosen_dir_path))


@click.group(cls=ReplGroup)
def repl():
    pass


@repl.command()
def pwd() -> None:
    global current_dir
    click.echo(get_sub_dir_path(current_dir))


@repl.command(cls=ReplCommand)
@click.argument('dir', required=False)
@click.option('-r', '--recursive', 'is_recursive', is_flag=True)
def ls(target_dir_path: str, is_recursive: bool) -> None:
    global current_dir, previous_dir, root_dir
    target_dir = current_dir
    target_dir = dir_dive(current_dir, previous_dir, root_dir, target_dir_path)
    if target_dir_path and target_dir == current_dir:
        return
    fs.tree.render(target_dir, max_levels=(None if is_recursive else 0))
    

@repl.command(cls=ReplCommand)
@click.argument('dir', required=True)
def cd(target_dir_path: str) -> None:
    global current_dir, previous_dir, root_dir
    current_dir = dir_dive(current_dir, previous_dir, root_dir, target_dir_path)


@repl.command(cls=ReplCommand)
def exit() -> None:
    raise ReplExitSignal()


@repl.command(cls=ReplCommand)
@click.argument('dir', required=False)
def select(target_dir_path: str) -> None:
    global current_dir, previous_dir, root_dir
    if not dir_enumerate(current_dir, previous_dir, root_dir, target_dir_path):
        click.echo('Aborting selection...')
        return
    current_dir = dir_dive(current_dir, previous_dir, root_dir, target_dir_path)
    raise ReplFinishSignal()
    