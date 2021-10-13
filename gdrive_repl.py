from interactive_tempfs import InteractiveTempFS
from drive_data_manager import DriveDataManager
import constants
from pathlib import Path
import shlex
from typing import Dict, Any, Tuple
import click
from click.core import Context
from click.formatting import HelpFormatter
from click.exceptions import UsageError
import copy
import fs.tree
from gdrive_utils import dir_dive, dir_enumerate
from utils import get_input, get_sub_dir_path


_ddm: DriveDataManager
_itfs: InteractiveTempFS


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


def run_repl(target_local_dir_path: Path = None) -> Tuple[str, Dict[str, Dict[str, Any]]]:
    global _ddm, _itfs
    _ddm = DriveDataManager()
    _itfs = InteractiveTempFS(_ddm, target_local_dir_path)

    while True:
        user_input = get_input()
        user_args = shlex.split(user_input)
        pre_command_dir = _itfs.current_dir

        try:
            repl(user_args)
        except SystemExit:
            pass
        except ReplExitSignal:
            return ''
        except ReplFinishSignal:
            break
        
        if pre_command_dir != _itfs.current_dir:
            _itfs.previous_dir = pre_command_dir

    chosen_dir = get_sub_dir_path(_itfs.current_dir)
    data = { # TODO: cull data we don't need
        (key[len(chosen_dir):]) : value.metadata
        for (key, value) in _ddm.drive_files.items() 
        if chosen_dir in key 
           and chosen_dir != key
           and value['mimeType'] != constants.FOLDER_MIMETYPE
    }

    _itfs.close()

    return (chosen_dir, data)


@click.group(cls=ReplGroup)
def repl():
    pass


@repl.command()
def pwd() -> None:
    global _itfs
    click.echo(get_sub_dir_path(_itfs.current_dir))


@repl.command(cls=ReplCommand)
@click.argument('dir', required=False)
@click.option('-r', '--recursive', 'is_recursive', is_flag=True)
def ls(dir: str, is_recursive: bool) -> None:
    global _ddm, _itfs
    target_dir = _itfs.current_dir
    target_dir = dir_dive(_ddm, _itfs, dir)
    if dir and target_dir == _itfs.current_dir:
        return
    fs.tree.render(target_dir, max_levels=(None if is_recursive else 0))
    

@repl.command(cls=ReplCommand)
@click.argument('dir', required=True)
def cd(dir: str) -> None:
    global _ddm, _itfs
    _itfs.current_dir = dir_dive(_ddm, _itfs, dir)


@repl.command(cls=ReplCommand)
def exit() -> None:
    raise ReplExitSignal()


@repl.command(cls=ReplCommand)
@click.argument('dir', required=False)
def select(dir: str) -> None:
    global _ddm, _itfs
    if not dir_enumerate(_ddm, _itfs, dir):
        click.echo('Aborting selection...')
        return
    _itfs.current_dir = dir_dive(_ddm, _itfs, dir)
    raise ReplFinishSignal()
    