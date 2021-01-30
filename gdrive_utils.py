from utils import get_sub_dir_path, sanitise_fname
from fs.subfs import SubFS
from typing import List, Dict
from fs.tempfs import TempFS
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from pydrive.files import GoogleDriveFile
import constants
import json
from pathlib import Path

def get_drive_instance() -> GoogleDrive:
    gauth = GoogleAuth(settings_file=constants.GAUTH_SETTINGS_RELPATH)
    gauth.LocalWebserverAuth()
    return GoogleDrive(gauth)


def get_files_in_drive_dir(drive: GoogleDrive, dir_drive_id: str) -> List[GoogleDriveFile]:
    query = constants.GDRIVE_QUERY.format(dir_drive_id)
    return drive.ListFile({'q': query}).GetList()


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

