import click
from pathlib import Path
from gdrive_repl import start_repl
from click.core import Context
from utils import get_path

@click.group()
def sdr() -> None:
    """Top-level SourceDrive command"""

@sdr.command()
@click.argument('dir', required=False)
@click.option('-s, --search', 'should_search', is_flag=True)
@click.option('-f, --force', 'is_forced', is_flag=True)
@click.option('-i, --interactive', 'is_interactive', is_flag=True)
def pull(dir: str, should_search: bool, is_forced: bool, is_interactive: bool) -> None:
    """
    Safe-syncs the specified directory if it is marked as a SourceDrive repository.
    If no directory is provided, the current directory is used.
    """
    target_dir: Path = get_path(dir)
    print(target_dir)

@sdr.command()
@click.argument('dir', required=False)
@click.option('-p', '--pull', 'should_pull', is_flag=True)
@click.pass_context
def init(context: Context, dir: str, should_pull: bool) -> None:
    """
    Mark a local directory as a SourceDrive repository. 
    If no directory is provided, the working directory is used. 
    Opens a REPL for navigation through your Google Drive file-system to select a folder for SourceDrive to sync from
    """
    target_dir: Path = get_path(dir)
    sdr_dir_path = target_dir / '.sdr/'

    try:
        sdr_dir_path.mkdir()
    except FileExistsError:
        click.echo('The targeted directory is already a SourceDrive repository')
        return

    gdrive_fs = start_repl(sdr_dir_path)
    with (sdr_dir_path / 'gdrive.fs').open(mode='w') as gdrive_fs_file:
        gdrive_fs_file.write(gdrive_fs)

    if should_pull:
        context.invoke(pull, dir=dir, should_search=False, is_forced=False, is_interactive=False)
    

