from pathlib import Path

def get_path(dir: str = "") -> Path:
    return Path(dir) if dir else Path.cwd()