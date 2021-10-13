from drive_data_manager import DriveDataManager
from utils import get_sub_dir_path, sanitise_fname
from fs.subfs import SubFS
from typing import List, Dict
from fs.tempfs import TempFS
from fs.base import FS
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from pydrive.files import GoogleDriveFile
import constants
import json
from pathlib import Path
import click
from fs.errors import DirectoryExpected
import os


def _build_virtual_file(parent_dir: SubFS[TempFS], drive_file: GoogleDriveFile, ext: str) -> Dict[str, str]:
    df_meta = drive_file.metadata
    file_name: str = df_meta['title']
    file_name = sanitise_fname(file_name)
    if df_meta['mimeType'] == constants.FOLDER_MIMETYPE:
        parent_dir.makedir(file_name)
    else:
        parent_dir.touch(f'{file_name}{ext}')
    return {f'{get_sub_dir_path(parent_dir)}/{file_name}{ext}': drive_file}


def _get_export_extension(file_mimetype: str, file_export_format_defaults: Dict[str, str]) -> str:
    if file_mimetype == constants.FOLDER_MIMETYPE:
        return ''
    export_extension = (constants.DRIVE_EXPORT_MIMETYPES 
        .get(file_mimetype, {}) 
        .get('exports', {}) 
        .get(file_export_format_defaults.get(file_mimetype, None), ''))
    return (f'.{export_extension}' if export_extension else '')


def _populate_dir_if_empty(
        parent_dir: SubFS[FS], 
        drive: GoogleDrive, 
        drive_files: Dict[str, GoogleDriveFile]
    ) -> None:

    if parent_dir.isempty('/'):
        generate_files(parent_dir, drive, drive_files)


def _safe_open_direct_child(parent_dir: SubFS[FS], target_sub_dir: str) -> SubFS[FS]:
    children = [dir.name for dir in parent_dir.filterdir('/', exclude_files=['*'])]
    if target_sub_dir in children: # ensure case sensistivity
        return parent_dir.opendir(target_sub_dir)
    raise DirectoryExpected(path='', msg=constants.DIRECTORY_EXPECTED_ERROR_MSG.format(target_sub_dir))


def get_drive_instance() -> GoogleDrive:
    gauth = GoogleAuth(settings_file=constants.GAUTH_SETTINGS_RELPATH)
    gauth.LocalWebserverAuth()
    return GoogleDrive(gauth)


def get_files_in_drive_dir(drive: GoogleDrive, dir_drive_id: str) -> List[GoogleDriveFile]:
    query = constants.GDRIVE_QUERY.format(dir_drive_id)
    return drive.ListFile({'q': query}).GetList()


def add_drive_files_to_sub_fs(parent_dir: SubFS[TempFS], files: List[GoogleDriveFile]) -> Dict[str, str]:
    google_ids = {}
    file_export_format_defaults: Dict[str, str] = {}
    with Path(constants.SDR_CONFIG_RELPATH).open('r') as sdr_config_file:
        file_export_format_defaults = json.load(sdr_config_file)['export_types']
    for file in files:
        google_ids.update(_build_virtual_file(parent_dir, file, _get_export_extension(
            file.metadata['mimeType'], file_export_format_defaults)
        ))
    return google_ids


def generate_files(parent_dir: SubFS[FS], ddm: DriveDataManager) -> None:
    files = get_files_in_drive_dir(ddm.drive, ddm.drive_files[get_sub_dir_path(parent_dir)]['id'])
    ddm.drive_files.update(add_drive_files_to_sub_fs(parent_dir, files))


def dir_dive(
        start_dir: SubFS[FS], 
        previous_dir: SubFS[FS], 
        root_dir: FS, 
        drive: GoogleDrive, 
        drive_files: Dict[str, GoogleDriveFile], 
        target_dir_path: str
    ) -> SubFS[FS]:

    if not target_dir_path:
        return start_dir

    current_dir = start_dir

    if target_dir_path == '-': # handle back-navigation case
        return previous_dir
    
    if target_dir_path[0] == '/': # handle absolute/home pathing
        current_dir = root_dir
        target_dir_path = target_dir_path[1:]
    elif target_dir_path[0] == '~':
        if len(target_dir_path) > 1:
            if target_dir_path[1] == '/':
                current_dir = root_dir.opendir('~')
                target_dir_path = target_dir_path[2:]

    target_dir_path = target_dir_path.rstrip(os.sep) 
    if len(target_dir_path) == 0: # early return for root/home path
        return current_dir

    dir_path = target_dir_path.split(os.sep)

    if '' in dir_path: # terminate if double-separators are present
        click.echo(constants.DIRECTORY_EXPECTED_ERROR_MSG.format(''))
        return start_dir

    while dir_path:
        _populate_dir_if_empty(current_dir, drive, drive_files)
        target_sub_dir = dir_path[0]
        if target_sub_dir == '..':
            try:
                current_dir = current_dir._wrap_fs
                del dir_path[0]
                continue
            except AttributeError:
                click.echo(constants.INVALID_BACKREFERENCE_ERROR_MSG)
                return start_dir
        try:
            current_dir = _safe_open_direct_child(current_dir, target_sub_dir)
        except DirectoryExpected as de:
            click.echo(de._msg)
            return start_dir
        del dir_path[0]
    _populate_dir_if_empty(current_dir, drive, drive_files)

    return current_dir


def dir_enumerate(
        start_dir: SubFS[FS],
        previous_dir: SubFS[FS],
        root_dir: FS,
        drive: GoogleDrive,
        drive_files: Dict[str, GoogleDriveFile], 
        target_dir_path: str = ''
    ) -> bool:

    target_dir = start_dir
    if target_dir_path:
        target_dir = dir_dive(start_dir, previous_dir, root_dir, drive, drive_files, target_dir_path)
        if target_dir == start_dir:
            return False
    for sub_dir_info in target_dir.filterdir('/', exclude_files=['*']):
        dir_enumerate(
            dir_dive(target_dir, previous_dir, root_dir, drive, drive_files, sub_dir_info.name), 
            previous_dir, 
            root_dir, 
            drive, 
            drive_files
        )
    return True
