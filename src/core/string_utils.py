from pathlib import Path
import time


def generate_valid_filename(path: Path, prefix: str = "", extension: str = "") -> Path:
    filename = Path(f"{prefix}{time.strftime('%Y%m%d_%H%M%S')}.{extension}")
    count: int = 1
    while (path / filename).exists() and (path / filename).is_file():
        name = filename.stem.rsplit('_', 1)[0] if count > 1 else filename.stem
        new_name: str = f"{name}_{count}{filename.suffix}"
        filename = filename.with_name(new_name)
        count += 1
    return path / filename
