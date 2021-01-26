from fs.base import FS
from fs.subfs import SubFS
from typing import List
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from pydrive.files import GoogleDriveFile
from constants import FOLDER_MIMETYPE
from dataclasses import dataclass

def get_drive_instance() -> GoogleDrive:
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()
    return GoogleDrive(gauth)


def get_files_in_drive_dir(drive: GoogleDrive, dir_drive_id: str) -> List[GoogleDriveFile]:
    query = f"'{dir_drive_id}' in parents and trashed=false"
    return drive.ListFile({'q': query}).GetList()


def _build_virtual_file(parent_dir: FS, drive_file: GoogleDriveFile) -> None:
    df_meta = drive_file.metadata
    file_name = df_meta['title']
    if df_meta['mimeType'] == FOLDER_MIMETYPE:
        parent_dir.makedir(file_name)
    else:
        parent_dir.touch(file_name)
    parent_dir.setinfo(file_name, {'google': {'id': df_meta['id']}})


def add_drive_files_to_sub_fs(parent_dir: FS, files: List[GoogleDriveFile]) -> None:
    for file in files:
        _build_virtual_file(parent_dir, file)

