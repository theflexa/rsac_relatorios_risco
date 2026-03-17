from rsac_relatorios_risco.performer.models import PerformerItem


ELIGIBLE_STATUSES = {"pendente", "erro sistêmico", "exceção negocial"}


def is_item_eligible(status: str, attempt_count: int, max_attempts: int) -> bool:
    return status in ELIGIBLE_STATUSES and attempt_count < max_attempts


def filter_eligible_items(
    items: list[PerformerItem],
    max_attempts: int,
) -> list[PerformerItem]:
    return [
        item
        for item in items
        if is_item_eligible(item.status, len(item.attempts), max_attempts)
    ]
