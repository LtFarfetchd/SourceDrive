import click
from pathlib import Path
from gdrive_repl import run_repl
from click.core import Context
from utils import get_path, get_input
import json
from constants import DRIVE_EXPORT_MIMETYPES
from typing import Dict, Any


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
    Safe-sync the specified directory if it is marked as a SourceDrive repository.
    If no directory is provided, the current directory is used.
    """
    target_dir: Path = get_path(dir)
    print(target_dir)


@sdr.command()
@click.argument('dir', required=False)
def configure(dir: str) -> None:
    """
    Interactively override default SourceDrive configurations.
    """
    config_dir = get_path(dir) / '.sdr' / 'config.json'
    if not (config_dir).exists():
        click.echo('Cannot modify configurations of an uninitialised SourceDrive repository')
        click.echo('Run `sdr init --help` for help with initialisation')

    with config_dir.open(mode='r+') as config_file:
        config: Dict[str, Any] = json.load(config_file)

        # configure default export types
        click.echo('Configuring default export formats')
        new_exports = {}
        for i, (key, value) in enumerate(DRIVE_EXPORT_MIMETYPES.items()):
            possible_exports: Dict[str, str] = value['exports']
            if not possible_exports:
                continue
            start_export_mimetype = config['export_types'][key]
            click.echo(f'\nCurrent default for google {value["name"]}s is (.{possible_exports[start_export_mimetype]})')
            click.echo('Update default export format (y/n)?')
            if get_input().lower() == 'y':
                enumerated_alternatives = list(enumerate(filter(lambda item: item[0] != start_export_mimetype, possible_exports.items())))
                click.echo(f'Alternative exports available:')
                click.echo('\n'.join([f'{j}: .{value} ({key})' for (j, (key, value)) in enumerated_alternatives]))
                click.echo('Select an export type by number (or enter to skip):')
                try:
                    selection = int(get_input())
                    new_exports[key] = enumerated_alternatives[selection][1][0]
                    continue
                except Exception:
                    pass
            new_exports[key] = start_export_mimetype
            click.echo('Skipping...')
        config['export_types'] = new_exports

        # write out
        config_file.seek(0)
        config_file.write(json.dumps(config, indent=4, sort_keys=True))
        config_file.truncate()
        


@sdr.command()
@click.argument('dir', required=False)
@click.option('-p', '--pull', 'should_pull', is_flag=True)
@click.option('-c', '--configure', 'should_configure', is_flag=True)
@click.pass_context
def init(context: Context, dir: str, should_pull: bool, should_configure: bool) -> None:
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
    
    with (sdr_dir_path / 'config.json').open(mode='w') as config_file:
        config_file.write(
            json.dumps(
                {'export_types': {key:value['default_export'] for (key, value) in DRIVE_EXPORT_MIMETYPES.items()}}
                ,indent=4
                ,sort_keys=True
            )
        )
    
    if should_configure:
        context.invoke(configure)

    gdrive_data = run_repl(sdr_dir_path)
    if gdrive_data:
        with (sdr_dir_path / 'gdrive.json').open(mode='w') as gdrive_fs_file:
            gdrive_fs_file.write(json.dumps(gdrive_data))
        if should_pull:
            context.invoke(pull, dir=dir, should_search=False, is_forced=False, is_interactive=False)
