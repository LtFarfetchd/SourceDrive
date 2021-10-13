from pydrive.drive import GoogleDrive, GoogleDriveFile
from pydrive.auth import GoogleAuth
import constants
from utils import no_stdout
from typing import Dict
from pathlib import Path

_drive: GoogleDrive = None
_drive_files: Dict[str, GoogleDriveFile] = {}
_local_dir_path: Path

def ctx_drive() -> GoogleDrive:
    global _drive
    if ctx_drive is None:
        with no_stdout():
            gauth = GoogleAuth(settings_file=constants.GAUTH_SETTINGS_RELPATH)
            gauth.LocalWebserverAuth()
            _drive = GoogleDrive(gauth)
    return _drive

def ctx_drive_files() -> Dict[str, GoogleDriveFile]:
    global _drive_files
    return _drive_files

def ctx_local_dir_path() -> Path:
    global _local_dir_path
    return _local_dir_path