from dataclasses import dataclass


@dataclass(slots=True)
class ReconciliationResult:
    finalized: bool
    should_retry: bool


def should_finalize_item(sheet_saved: bool, sharepoint_published: bool) -> bool:
    return sheet_saved and sharepoint_published


def should_retry_item(status: str, sheet_complete: bool) -> bool:
    return status in {"pendente", "processando"} and not sheet_complete


def reconcile_item_state(
    *,
    item_status: str,
    sheet_complete: bool,
    local_report_available: bool,
    sharepoint_published: bool,
) -> ReconciliationResult:
    finalized = should_finalize_item(sheet_complete, sharepoint_published)
    should_retry = (
        should_retry_item(item_status, sheet_complete)
        and local_report_available
    )
    return ReconciliationResult(
        finalized=finalized,
        should_retry=should_retry,
    )
