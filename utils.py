from pathlib import Path
from fs.tempfs import TempFS
from fs.info import Info
from typing import Dict, Text, Any, Optional, Collection

def get_path(dir: str = "") -> Path:
    return Path(dir) if dir else Path.cwd()

class DriveFS(TempFS):
    def __init__(self, 
        identifier: Text = "__tempfs__", 
        temp_dir: Optional[Text] = None,   
        auto_clean: bool = True,   
        ignore_clean_errors: bool = True  
    ) -> None:
        super().__init__(identifier=identifier, temp_dir=temp_dir, auto_clean=auto_clean, ignore_clean_errors=ignore_clean_errors)
        self._google_info = {}


    def setinfo(self, path: Text, info: Dict[str, Dict[str, Any]]) -> None:
        super().setinfo(path, info)
        self._google_info = info['google']


    def getinfo(self, path: Text, namespaces: Optional[Collection[Text]] = None) -> Info:
        info = (super().getinfo(path, namespaces=namespaces)).raw
        info['google'] = self._google_info
        return Info(info)
