from datetime import datetime, timedelta
from pathlib import Path

from rsac_relatorios_risco.services.cleanup_service import delete_files_older_than


def test_delete_files_older_than_removes_only_old_files(tmp_path: Path):
    old_file = tmp_path / "old.xlsx"
    recent_file = tmp_path / "recent.xlsx"
    old_file.write_text("old", encoding="utf-8")
    recent_file.write_text("recent", encoding="utf-8")

    old_time = (datetime.now() - timedelta(days=16)).timestamp()
    recent_time = (datetime.now() - timedelta(days=5)).timestamp()

    old_file.touch()
    recent_file.touch()
    import os
    os.utime(old_file, (old_time, old_time))
    os.utime(recent_file, (recent_time, recent_time))

    deleted_files = delete_files_older_than(tmp_path, days=15)

    assert deleted_files == [str(old_file)]
    assert old_file.exists() is False
    assert recent_file.exists() is True
