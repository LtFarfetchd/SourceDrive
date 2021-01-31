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
from fs.base import FS
from fs.tempfs import TempFS
from fs.subfs import SubFS
from pydrive.drive import GoogleDrive
from pydrive.files import GoogleDriveFile
from gdrive_utils import get_drive_instance, generate_files, dir_dive, dir_enumerate
from utils import get_input, get_sub_dir_path, no_stdout


drive: GoogleDrive
root_dir: TempFS
previous_dir: SubFS[FS]
current_dir: SubFS[FS]
drive_files: Dict[str, GoogleDriveFile] = {}


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


def run_repl(target_dir_path: Path) -> Tuple[str, Dict[str, Dict[str, Any]]]:
    global drive, root_dir, current_dir, previous_dir, drive_files
    with no_stdout():
        drive = get_drive_instance()
    temp_dir_path = (target_dir_path / constants.TEMP_DIR_RELPATH)
    temp_dir_path.mkdir()
    root_dir = TempFS(temp_dir=str(temp_dir_path.resolve()))
    current_dir = root_dir.makedir('~')
    drive_files[current_dir._sub_dir] = GoogleDriveFile(metadata={'id': 'root'})
    generate_files(current_dir, drive, drive_files)
    previous_dir = current_dir

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

    chosen_dir = get_sub_dir_path(current_dir)
    data = { # TODO: cull data we don't need
        (key[len(chosen_dir):]) : value.metadata
        for (key, value) in drive_files.items() 
        if chosen_dir in key 
           and chosen_dir != key
           and value['mimeType'] != constants.FOLDER_MIMETYPE
    }

    root_dir.close()
    temp_dir_path.rmdir()

    return (chosen_dir, data)


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
def ls(dir: str, is_recursive: bool) -> None:
    global current_dir, previous_dir, root_dir, drive_files, drive
    target_dir = current_dir
    target_dir = dir_dive(current_dir, previous_dir, root_dir, drive, drive_files, dir)
    if dir and target_dir == current_dir:
        return
    fs.tree.render(target_dir, max_levels=(None if is_recursive else 0))
    

@repl.command(cls=ReplCommand)
@click.argument('dir', required=True)
def cd(dir: str) -> None:
    global current_dir, previous_dir, root_dir, drive_files, drive
    current_dir = dir_dive(current_dir, previous_dir, root_dir, drive, drive_files, dir)


@repl.command(cls=ReplCommand)
def exit() -> None:
    raise ReplExitSignal()


@repl.command(cls=ReplCommand)
@click.argument('dir', required=False)
def select(dir: str) -> None:
    global current_dir, previous_dir, root_dir, drive_files, drive
    if not dir_enumerate(current_dir, previous_dir, root_dir, drive, drive_files, dir):
        click.echo('Aborting selection...')
        return
    current_dir = dir_dive(current_dir, previous_dir, root_dir, drive, drive_files, dir)
    raise ReplFinishSignal()
    