from rsac_relatorios_risco.performer.reconciliation import (
    reconcile_item_state,
    should_finalize_item,
    should_retry_item,
)


def test_should_finalize_item_requires_saved_sheet_and_published_sharepoint():
    assert should_finalize_item(sheet_saved=True, sharepoint_published=True) is True
    assert should_finalize_item(sheet_saved=True, sharepoint_published=False) is False
    assert should_finalize_item(sheet_saved=False, sharepoint_published=True) is False


def test_should_retry_item_only_for_pending_or_in_progress_with_incomplete_sheet():
    assert should_retry_item(status="aguardando", sheet_complete=False) is True
    assert should_retry_item(status="em andamento", sheet_complete=False) is True
    assert should_retry_item(status="finalizado", sheet_complete=False) is False
    assert should_retry_item(status="aguardando", sheet_complete=True) is False


def test_reconcile_item_state_uses_sharepoint_for_finalize_and_local_report_for_retry():
    result = reconcile_item_state(
        item_status="em andamento",
        sheet_complete=True,
        local_report_available=True,
        sharepoint_published=False,
    )

    assert result.finalized is False
    assert result.should_retry is False

    retry_result = reconcile_item_state(
        item_status="aguardando",
        sheet_complete=False,
        local_report_available=True,
        sharepoint_published=False,
    )

    assert retry_result.finalized is False
    assert retry_result.should_retry is True
