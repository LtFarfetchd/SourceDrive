# TODO: use constants for error messages and dictionary keys

import os

from fs.tempfs import TempFS
from gdrive_utils import (
    dir_enumerate, 
    generate_init_data, 
    generate_init_resources
)
from json.decoder import JSONDecodeError
import click
from pathlib import Path
from gdrive_repl import run_repl
from click.core import Context
from utils import get_path, get_input, no_stdout
import json
import constants
from typing import Dict, Any
from drive_context import ctx_drive, ctx_drive_files, ctx_local_dir_path


@click.group()
def sdr() -> None:
    """Top-level SourceDrive command"""


@sdr.command()
@click.argument('dir', required=False)
@click.option('-s, --search', 'should_search', is_flag=True)
@click.option('-f, --force', 'is_forced', is_flag=True)
@click.option('-i, --interactive', 'is_interactive', is_flag=True)
@click.option('--fetch/--no-fetch', default=True)
def pull(dir: str, should_search: bool, is_forced: bool, is_interactive: bool, fetch: bool) -> None:
    """
    Safe-sync the specified directory if it is marked as a SourceDrive repository.
    If no directory is provided, the current directory is used.
    """
    target_dir_path = ctx_local_dir_path() = get_path(dir)
    drive = ctx_drive()

    sdr_config: Dict[str, Any] = {}
    export_defaults: Dict[str, str] = {}
    chosen_gdrive_dir_path: str
    with (target_dir_path / constants.SDR_CONFIG_RELPATH).open('r') as sdr_config_file:
        try:
            sdr_config = json.load(sdr_config_file)
        except JSONDecodeError:
            click.echo('Could not parse SourceDrive configurations from `config.json`. \
                Run `sdr configure` to attempt to fix configurations.')
            return
        try:
            chosen_gdrive_dir_path = sdr_config[constants.CHOSEN_GDRIVE_DIR_PATH_KEY]
        except KeyError:
            click.echo('Error: Could not read targeted Google Drive directory from `config.json`. \
                Run `sdr init` to initialise a repository.')
            return
        try:
            export_defaults = ['export_types']
        except KeyError:
            click.echo('Error: Could not read default export types from `config.json`. \
                Run `sdr configure` to attempt to fix configurations.')
            return
    
    remote_data: Dict[str, Dict[str, Any]]
    if fetch:
        root_dir, current_dir, previous_dir = generate_init_resources()
        dir_enumerate(current_dir, previous_dir, root_dir, chosen_gdrive_dir_path)
        remote_data = generate_init_data(chosen_gdrive_dir_path)
    else:
        pass # just use the specific ids to identify pull down new versions of files where necessary
            
    # read out the drive files' configs
    local_drive_files: Dict[str, Any] = {}
    with (target_dir_path / constants.DRIVE_FILES_RELPATH).open('r') as drive_files_file:
        local_drive_files = json.load(drive_files_file)

    for path, drive_file_metadata in local_drive_files.items():
        if drive_file_metadata['mimeType'] == constants.FOLDER_MIMETYPE:
            continue
        current_file = drive.CreateFile(metadata=drive_file_metadata)
        abs_file_path = Path(path.strip(os.sep)).resolve()
        abs_file_path.parent.mkdir(parents=True, exist_ok=True)
        current_file.GetContentFile(str(abs_file_path), mimetype=export_defaults.get(current_file['mimeType'], None))


@sdr.command()
@click.argument('dir', required=False)
def configure(dir: str) -> None:
    """
    Interactively override default SourceDrive configurations.
    """
    # TODO: attempt to repair broken configs if file exists but can't be parsed
    config_dir = get_path(dir) / constants.SDR_CONFIG_RELPATH
    if not (config_dir).exists():
        click.echo('Cannot modify configurations of an uninitialised SourceDrive repository')
        click.echo('Run `sdr init --help` for help with initialisation')

    with config_dir.open(mode='r+') as config_file:
        config: Dict[str, Any] = json.load(config_file)

        # configure default export types
        click.echo('Configuring default export formats')
        new_exports = {}
        for i, (key, value) in enumerate(constants.DRIVE_EXPORT_MIMETYPES.items()):
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
@click.argument('creds', required=True)
@click.option('-lD', '--local-dir', type=str)
@click.option('-dD', '--drive-dir', type=str)
@click.option('-p', '--pull', 'should_pull', is_flag=True)
@click.option('-c', '--configure', 'should_configure', is_flag=True)
@click.pass_context
def init(
        context: Context, 
        creds: str, 
        local_dir: str, 
        drive_dir: str, 
        should_pull: bool, 
        should_configure: bool
    ) -> None:

    """
    Mark a local directory as a SourceDrive repository. 
    If no directory is provided, the working directory is used. 
    Opens a REPL for navigation through your Google Drive file-system to select a folder for SourceDrive to sync from
    """
    target_dir_path: Path = get_path(local_dir)


    # fetch google OAuth credentials
    gauth_credentials = ''
    creds_are_valid = True
    try:
        with Path(creds).open('r') as user_gauth_credentials_file:
            gauth_credentials = json.load(user_gauth_credentials_file)
    except JSONDecodeError:
        creds_are_valid = False
    except FileNotFoundError:
        try:
            gauth_credentials = json.loads(creds)
        except JSONDecodeError:
            creds_are_valid = False
    
    if not creds_are_valid:
        click.echo('Invalid Google Authentication credentials. \
            The raw JSON or indicated JSON file could not be parsed.')
    if 'web' not in gauth_credentials:
        click.echo('Invalid Google Authentication credentials. \
            The raw JSON or indicated JSON file does not contain valid Google OAuth credentials.')
        return

    try:
        (target_dir_path / constants.SDR_RELPATH).mkdir()
    except FileExistsError:
        click.echo('The targeted directory is already a SourceDrive repository')
        return

    # write out GAuth settings
    with (target_dir_path / constants.GAUTH_SETTINGS_RELPATH).open(mode='w') as gauth_settings_file:
        gauth_settings_file.write(constants.GAUTH_SETTINGS)

    # write out GAuth credentials (secrets)
    with (target_dir_path / constants.GAUTH_CREDENTIALS_RELPATH).open(mode='w') as gauth_credentials_file:
        gauth_credentials_file.write(json.dumps(gauth_credentials))
    
    # write out SDR config
    with (target_dir_path / constants.SDR_CONFIG_RELPATH).open(mode='w') as config_file:
        config_file.write(
            json.dumps(
                {'export_types': {key:value['default_export'] for (key, value) in constants.DRIVE_EXPORT_MIMETYPES.items()}}
                ,indent=4
                ,sort_keys=True
            )
        )
    
    if should_configure:
        context.invoke(configure, dir=local_dir)

    # auto-generate file data using CLI input or interactively selected drive directory
    if drive_dir:
        chosen_gdrive_dir_path = drive_dir
        root_dir, current_dir, previous_dir, drive, drive_files = generate_init_resources(target_dir_path)
        dir_enumerate(current_dir, previous_dir, root_dir, drive, drive_files, chosen_gdrive_dir_path)
        gdrive_data = generate_init_data(chosen_gdrive_dir_path)
    else:
        chosen_gdrive_dir_path, gdrive_data = run_repl(target_dir_path)

    if gdrive_data:
        # write out path
        with (target_dir_path / constants.SDR_CONFIG_RELPATH).open(mode='r+') as sdr_config_file:
            sdr_config: Dict[str, Any] = json.load(sdr_config_file)
            sdr_config.update({constants.CHOSEN_GDRIVE_DIR_PATH_KEY: chosen_gdrive_dir_path})
            sdr_config_file.seek(0)
            sdr_config_file.write(json.dumps(sdr_config, indent=4, sort_keys=True))

        # write out data
        with (target_dir_path / constants.DRIVE_FILES_RELPATH).open(mode='w') as gdrive_fs_file:
            gdrive_fs_file.write(json.dumps(gdrive_data))
        if should_pull:
            context.invoke(pull, dir=local_dir, should_search=False, is_forced=False, is_interactive=False)
