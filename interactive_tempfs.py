from fs.subfs import SubFS
from fs.tempfs import TempFS
from fs.base import FS
from pydrive.drive import GoogleDriveFile
import constants
from pathlib import Path
from drive_data_manager import DriveDataManager
from gdrive_utils import generate_files

class InteractiveTempFS:
    def __init__(self, ddm: DriveDataManager, target_local_dir_path: Path = None):
        if not target_local_dir_path is None:
            temp_dir_path = (target_local_dir_path / constants.TEMP_DIR_RELPATH).resolve()
            if not temp_dir_path.exists():
                temp_dir_path.mkdir()
        else:
            temp_dir_path = None
        self._root_dir = TempFS(temp_dir=str(temp_dir_path.resolve()))
        self._current_dir = self._root_dir.makedir('~')
        ddm.drive_files[self._current_dir._sub_dir] = GoogleDriveFile(metadata={'id': 'root'})
        generate_files(self._current_dir, ddm)
        self._previous_dir = self._current_dir

    @property
    def root_dir(self) -> TempFS:
        return self._root_dir
    
    @property
    def current_dir(self) -> TempFS | SubFS[FS]:
        return self._current_dir

    @property
    def previous_dir(self) -> TempFS | SubFS[FS]:
        return self._previous_dir
