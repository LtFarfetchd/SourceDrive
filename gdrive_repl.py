from pathlib import Path
import shlex
from typing import Dict
import click
from click.core import Context
from click.formatting import HelpFormatter
from click.exceptions import UsageError
import copy
from fs.base import FS
from fs.tempfs import TempFS
from fs.subfs import SubFS
from pydrive.drive import GoogleDrive
from gdrive_utils import get_drive_instance, get_files_in_drive_dir, add_drive_files_to_sub_fs
from utils import get_sub_dir_path

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

        print(gdrive_fs.tree())


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


@click.group(cls=ReplGroup)
def repl():
    pass


@repl.command(cls=ReplCommand)
@click.argument('dir', required=True)
def cd(dir: str) -> SubFS:
    global current_dir
    while not current_dir.exists(dir):
        split_dir = shlex.split(dir)
        next_dir, dir = split_dir[0], split_dir[1:]
        if not current_dir.exists(next_dir):
            _generate_files(current_dir)
        current_dir = current_dir.opendir(next_dir)
    current_dir = current_dir.opendir(dir)
    _generate_files(current_dir)
    