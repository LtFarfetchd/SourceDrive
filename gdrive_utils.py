import os
from utils import get_sub_dir_path, sanitise_fname
from fs.subfs import SubFS
from typing import List, Dict
from pathlib import Path
from fs.tempfs import TempFS
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from pydrive.files import GoogleDriveFile
from constants import FOLDER_MIMETYPE

def get_drive_instance() -> GoogleDrive:
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()
    return GoogleDrive(gauth)


def get_files_in_drive_dir(drive: GoogleDrive, dir_drive_id: str) -> List[GoogleDriveFile]:
    query = f"'{dir_drive_id}' in parents and trashed=false"
    return drive.ListFile({'q': query}).GetList()


def _build_virtual_file(parent_dir: SubFS[TempFS], drive_file: GoogleDriveFile) -> Dict[str, str]:
    df_meta = drive_file.metadata
    file_name: str = df_meta['title']
    file_name = sanitise_fname(file_name)
    if df_meta['mimeType'] == FOLDER_MIMETYPE:
        parent_dir.makedir(file_name)
    else:
        parent_dir.touch(file_name)
    return {f'{get_sub_dir_path(parent_dir)}/{file_name}': drive_file}

def add_drive_files_to_sub_fs(parent_dir: SubFS[TempFS], files: List[GoogleDriveFile]) -> Dict[str, str]:
    google_ids = {}
    for file in files:
        google_ids.update(_build_virtual_file(parent_dir, file))
    return google_ids

