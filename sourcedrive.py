import click
from pathlib import Path

def _get_path(dir: str = "") -> Path:
    return Path(dir) if dir else Path.cwd()

@click.group()
def sdr() -> None:
    """Top-level SourceDrive command"""

@sdr.command()
@click.argument('dir', required=False)
@click.option('-r, --recursive', 'is_recursive')
@click.option('-f, --force', 'is_forced')
@click.option('-i, --interactive', 'is_interactive')
def pull(dir: str, is_recursive: bool, is_forced: bool, is_interactive: bool) -> None:
    """Safe-syncs the specified directory if it is marked as a SourceDrive repository.
    If no directory is provided, the current directory is used."""
    target_dir: Path = _get_path(dir)
    print(target_dir)

@sdr.command()
@click.argument('dir', required=False)
def init(dir: str) -> None:
    """Mark a local directory as a SourceDrive repository. 
    If no directory is provided, the working directory is used. 
    Opens a REPL for navigation through your Google Drive file-system to select a folder for SourceDrive to sync from"""
    target_dir: Path = _get_path(dir)
    print(target_dir)

