def should_publish_incrementally(workbook_exists: bool) -> bool:
    return workbook_exists


def build_incremental_destination(base_path: str, workbook_name: str) -> str:
    return f"{base_path.rstrip('/')}/{workbook_name}"
