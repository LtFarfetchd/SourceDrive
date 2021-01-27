import os
from pathlib import Path
import shlex
from typing import Dict
import click
from click.core import Context
from click.formatting import HelpFormatter
from click.exceptions import UsageError
import copy
import fs.tree
from fs.base import FS
from fs.tempfs import TempFS
from fs.subfs import SubFS
from pydrive.drive import GoogleDrive
from gdrive_utils import get_drive_instance, get_files_in_drive_dir, add_drive_files_to_sub_fs
from utils import get_sub_dir_path


class ReplExitSignal(Exception):
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


drive: GoogleDrive
current_dir: SubFS[FS]
drive_ids: Dict[str, str] = {}


def _generate_files(parent_dir: SubFS[FS]) -> None:
    global drive, drive_ids
    files = get_files_in_drive_dir(drive, drive_ids[get_sub_dir_path(parent_dir)])
    drive_ids.update(add_drive_files_to_sub_fs(parent_dir, files))


def _parentless(context: Context) -> Context:
    ctx = copy.deepcopy(context)
    ctx.parent = None
    return ctx


def _dive(start_dir: SubFS[FS], target_dir_path: str) -> SubFS[FS]:
    # TODO: handle back-reference (..) instances within path
    current_dir = start_dir
    if current_dir.exists(target_dir_path):
        current_dir = current_dir.opendir(target_dir_path)
        if current_dir.isempty('/'):
            _generate_files(current_dir)
        return current_dir

    dir_path = target_dir_path.split(os.sep)
    while dir_path:
        if not current_dir.exists(dir_path[0]):
            _generate_files(current_dir)
        current_dir = current_dir.opendir(dir_path[0])
        del dir_path[0]
    _generate_files(current_dir)

    return current_dir


def start_repl(sdr_dir_path: Path) -> str:
    global drive, current_dir, drive_ids
    drive = get_drive_instance()
    temp_dir_path = (sdr_dir_path / 'temp/')
    temp_dir_path.mkdir()
    gdrive_fs = TempFS(temp_dir=str(temp_dir_path.resolve()))
    current_dir = gdrive_fs.makedir('~')
    drive_ids[current_dir._sub_dir] = 'root'
    _generate_files(current_dir)

    while True:
        user_input = input('> ')
        user_args = shlex.split(user_input)

        try:
            repl(user_args)
        except SystemExit:
            pass
        except ReplExitSignal:
            break

    return ''


@click.group(cls=ReplGroup)
def repl():
    pass


@repl.command(cls=ReplCommand)
@click.argument('dir', required=False)
@click.option('-r', '--recursive', 'is_recursive', is_flag=True)
def ls(dir: str, is_recursive: bool) -> None:
    global current_dir
    target_dir = current_dir
    if dir:
        target_dir = _dive(current_dir, dir)

    fs.tree.render(target_dir, max_levels=(None if is_recursive else 0))
    

@repl.command(cls=ReplCommand)
@click.argument('dir', required=True)
def cd(dir: str) -> None:
    global current_dir
    current_dir = _dive(current_dir, dir)


@repl.command(cls=ReplCommand)
def exit() -> None:
    raise ReplExitSignal()
    