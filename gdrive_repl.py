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
from pydrive.files import GoogleDriveFile
from gdrive_utils import get_drive_instance, get_files_in_drive_dir, add_drive_files_to_sub_fs
from utils import get_sub_dir_path


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


drive: GoogleDrive
previous_dir: SubFS[FS]
current_dir: SubFS[FS]
drive_files: Dict[str, GoogleDriveFile] = {}


def _generate_files(parent_dir: SubFS[FS]) -> None:
    global drive, drive_files
    files = get_files_in_drive_dir(drive, drive_files[get_sub_dir_path(parent_dir)]['id'])
    drive_files.update(add_drive_files_to_sub_fs(parent_dir, files))


def _parentless(context: Context) -> Context:
    ctx = copy.deepcopy(context)
    ctx.parent = None
    return ctx


def _dive(start_dir: SubFS[FS], target_dir_path: str) -> SubFS[FS]:
    # TODO: handle back-reference (..) instances within path
    global previous_dir

    if target_dir_path == '-': # handle back-navigation case
        return previous_dir

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


def _enumerate(start_dir: SubFS[FS]) -> None:
    if start_dir.isempty('/'):
        _generate_files(start_dir)
    for sub_dir_info in start_dir.filterdir('/', exclude_files=['*']):
        _enumerate(start_dir.opendir(sub_dir_info.name))


def run_repl(sdr_dir_path: Path) -> Dict[str, str]:
    global drive, current_dir, previous_dir, drive_files
    drive = get_drive_instance()
    temp_dir_path = (sdr_dir_path / 'temp/')
    temp_dir_path.mkdir()
    gdrive_fs = TempFS(temp_dir=str(temp_dir_path.resolve()))
    current_dir = gdrive_fs.makedir('~')
    drive_files[current_dir._sub_dir] = GoogleDriveFile(metadata={'id': 'root'})
    _generate_files(current_dir)
    previous_dir = current_dir

    while True:
        user_input = input('> ')
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

    chosen_dir = get_sub_dir_path(current_dir)
    data = { # TODO: cull data we don't need
        (key[len(chosen_dir):]) : value.metadata
        for (key, value) in drive_files.items() 
        if chosen_dir in key and chosen_dir != key
    }

    gdrive_fs.close()
    temp_dir_path.rmdir()

    return data


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


@repl.command(cls=ReplCommand)
@click.argument('dir', required=False)
def select(dir: str) -> None:
    global current_dir
    if dir:
        current_dir = _dive(current_dir, dir)
    _enumerate(current_dir)
    raise ReplFinishSignal()
    