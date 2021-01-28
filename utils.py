import os
from pathlib import Path
from fs.base import FS
from fs.subfs import SubFS

def get_path(dir: str = "") -> Path:
    return Path(dir) if dir else Path.cwd()


def get_sub_dir_path(dir: SubFS[FS]) -> str:
    try:
        return get_sub_dir_path(dir._wrap_fs) + dir._sub_dir
    except AttributeError:
        return ''

def sanitise_fname(path: str) -> str:
    return path.replace(os.sep, '+')