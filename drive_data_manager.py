
from gdrive_utils import get_drive_instance
from utils import no_stdout
from pydrive.drive import GoogleDrive, GoogleDriveFile
from typing import Dict

class DriveDataManager:
    def __init__(self):
        with no_stdout():
            self._drive = get_drive_instance()
        self._drive_files = {}

    @property
    def drive_files(self) -> Dict[str, GoogleDriveFile]:
        return self._drive_files

    @property
    def drive(self) -> GoogleDrive:
        return self._drive
