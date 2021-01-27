from pathlib import Path
from fs.base import FS
from fs.subfs import SubFS

def get_path(dir: str = "") -> Path:
    return Path(dir) if dir else Path.cwd()


def get_sub_dir_path(dir: SubFS[FS]) -> str:
    path = ''
    try:
        path += dir._wrap_fs._sub_dir
    except AttributeError:
        pass
    path += dir._sub_dir
    return path