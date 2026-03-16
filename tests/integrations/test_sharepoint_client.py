from rsac_relatorios_risco.integrations.sharepoint_client import (
    build_incremental_destination,
    should_publish_incrementally,
)


def test_build_incremental_destination_appends_workbook_name_once():
    destination = build_incremental_destination(
        "https://tenant.sharepoint.com/sites/risco/2026-03/",
        "RSAC_032026.xlsx",
    )

    assert destination == "https://tenant.sharepoint.com/sites/risco/2026-03/RSAC_032026.xlsx"


def test_should_publish_incrementally_requires_existing_workbook():
    assert should_publish_incrementally(workbook_exists=True) is True
    assert should_publish_incrementally(workbook_exists=False) is False
