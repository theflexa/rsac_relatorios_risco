from datetime import datetime, timedelta
from pathlib import Path


def delete_files_older_than(base_dir: Path, days: int) -> list[str]:
    threshold = datetime.now() - timedelta(days=days)
    deleted_files: list[str] = []

    for path in base_dir.iterdir():
        if not path.is_file():
            continue
        modified_at = datetime.fromtimestamp(path.stat().st_mtime)
        if modified_at < threshold:
            path.unlink()
            deleted_files.append(str(path))

    return deleted_files
