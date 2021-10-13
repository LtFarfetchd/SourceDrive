from utils import get_sub_dir_path, sanitise_fname
from fs.subfs import SubFS
from typing import List, Dict, Any
from fs.tempfs import TempFS
from fs.base import FS
from pydrive.files import GoogleDriveFile
import constants
import json
import click
from fs.errors import DirectoryExpected
import os
from collections import namedtuple
from drive_context import ctx_drive as ctx_drive, ctx_drive_files as ctx_drive_files, ctx_local_dir_path as ctx_local_dir_path


InitResources = namedtuple('InitResources', 'root_dir current_dir previous_dir')


def _build_virtual_file(parent_dir: SubFS[TempFS], drive_file: GoogleDriveFile, ext: str) -> Dict[str, GoogleDriveFile]:
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


def _safe_open_direct_child(parent_dir: SubFS[FS], target_sub_dir: str) -> SubFS[FS]:
    children = [dir.name for dir in parent_dir.filterdir('/', exclude_files=['*'])]
    if target_sub_dir in children: # ensure case sensistivity
        return parent_dir.opendir(target_sub_dir)
    raise DirectoryExpected(path='', msg=constants.DIRECTORY_EXPECTED_ERROR_MSG.format(target_sub_dir))


def get_files_in_drive_dir(dir_drive_id: str) -> List[GoogleDriveFile]:
    query = constants.GDRIVE_QUERY.format(dir_drive_id)
    return ctx_drive().ListFile({'q': query}).GetList()


def add_drive_files_to_sub_fs(parent_dir: SubFS[TempFS], files: List[GoogleDriveFile]) -> Dict[str, str]:
    google_ids = {}
    file_export_format_defaults: Dict[str, str] = {}
    with (ctx_local_dir_path() / constants.SDR_CONFIG_RELPATH).open('r') as sdr_config_file:
        file_export_format_defaults = json.load(sdr_config_file)['export_types']
    for file in files:
        google_ids.update(_build_virtual_file(parent_dir, file, _get_export_extension(
            file.metadata['mimeType'], file_export_format_defaults)
        ))
    return google_ids


def populate_dir(target_dir: SubFS[FS]) -> None:
    if target_dir.isempty('/'):
        drive_files = ctx_drive_files()
        files = get_files_in_drive_dir(drive_files[get_sub_dir_path(target_dir)]['id'])
        drive_files.update(add_drive_files_to_sub_fs(target_dir, files))


def dir_dive(
        start_dir: SubFS[FS], 
        previous_dir: SubFS[FS], 
        root_dir: FS, 
        target_dir_path: str,
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
        populate_dir(current_dir)
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
    populate_dir(current_dir)

    return current_dir


def dir_enumerate(start_dir: SubFS[FS], previous_dir: SubFS[FS],
        root_dir: FS,
        target_dir_path: str = ''
    ) -> bool:

    target_dir = start_dir
    if target_dir_path:
        target_dir = dir_dive(start_dir, previous_dir, root_dir, target_dir_path)
        if target_dir == start_dir:
            return False
    for sub_dir_info in target_dir.filterdir('/', exclude_files=['*']):
        dir_enumerate(
            dir_dive(target_dir, previous_dir, root_dir, sub_dir_info.name), 
            previous_dir, 
            root_dir
        )
    return True


def generate_init_resources() -> InitResources:
    local_dir_path = ctx_local_dir_path()
    temp_dir_path = (local_dir_path / constants.TEMP_DIR_RELPATH)
    temp_dir_path.mkdir()
    root_dir = TempFS(temp_dir=str(temp_dir_path.resolve()))
    current_dir = root_dir.makedir('~')
    ctx_drive_files()[current_dir._sub_dir] = GoogleDriveFile(metadata={'id': 'root'})
    populate_dir(current_dir)
    return InitResources(root_dir, current_dir, current_dir)


def generate_init_data(chosen_dir_path: str) -> Dict[str, Dict[str, Any]]:
    return { # TODO: cull data we don't need
        (key[len(chosen_dir_path):]) : value.metadata
        for (key, value) in ctx_drive_files().items() 
        if chosen_dir_path in key 
           and chosen_dir_path != key
           and value['mimeType'] != constants.FOLDER_MIMETYPE
    }