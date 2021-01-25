from pathlib import Path
import shlex
import click
from click.core import Context, Parameter
from click.formatting import HelpFormatter
from click.exceptions import UsageError
import copy
from typing import List
from fs import tempfs
from fs.subfs import SubFS
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from pydrive.files import GoogleDriveFile
import os


def _get_drive_instance() -> GoogleDrive:
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()
    return GoogleDrive(gauth)


def _get_files_in_drive_dir(drive: GoogleDrive, dir_drive_id: str) -> List[GoogleDriveFile]:
    query = f"'{dir_drive_id}' in parents and trashed=false"
    return drive.ListFile({'q': query}).GetList()

def start_repl(sdr_dir_path: Path) -> str:
    drive = _get_drive_instance()
    temp_dir_path = (sdr_dir_path / 'temp/')
    temp_dir_path.mkdir()
    gdrive_fs = tempfs.TempFS(temp_dir=str(temp_dir_path.resolve()))
    current_dir: SubFS = gdrive_fs.makedir('root')

    while True:
        user_input = input('> ')
        user_args = [current_dir].extend(shlex.split(user_input))
        files = _get_files_in_drive_dir(drive, ((str(current_dir._sub_dir)).strip(os.sep)))
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
def cd(current_dir: SubFS, dir: str) -> None:
    click.echo(dir)

