import click
from pathlib import Path

from click.core import Context

def _get_path(dir: str = "") -> Path:
    return Path(dir) if dir else Path.cwd()

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
    target_dir: Path = _get_path(dir)
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
    target_dir: Path = _get_path(dir)
    if (target_dir / '.sdr').exists():
        click.echo('The targeted directory is already a SourceDrive repository')
        return
    
    

    if should_pull:
        context.invoke(pull, dir=dir, should_search=False, is_forced=False, is_interactive=False)
    

