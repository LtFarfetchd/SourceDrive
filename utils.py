import os
from pathlib import Path
from fs.base import FS
from fs.subfs import SubFS
import contextlib
import sys

def get_path(dir: str = "") -> Path:
    return Path(dir) if dir else Path.cwd()


def get_input() -> str:
    return input('> ')


def get_sub_dir_path(dir: SubFS[FS]) -> str:
    try:
        return get_sub_dir_path(dir._wrap_fs) + dir._sub_dir
    except AttributeError:
        return ''

def sanitise_fname(path: str) -> str:
    return path.replace(os.sep, '+')


@contextlib.contextmanager
def no_stdout():
    old_stdout = sys.stdout
    sys.stdout = open(os.devnull, 'w')
    yield
    sys.stdout = old_stdout