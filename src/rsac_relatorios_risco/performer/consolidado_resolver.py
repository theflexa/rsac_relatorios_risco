import shutil
from pathlib import Path


def resolve_monthly_workbook(
    *,
    template_path: Path,
    output_dir: Path,
    competencia: str,
    file_name: str,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    workbook_path = output_dir / file_name
    if workbook_path.exists():
        return workbook_path

    shutil.copy2(template_path, workbook_path)
    return workbook_path
