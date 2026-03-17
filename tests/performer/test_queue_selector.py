from rsac_relatorios_risco.performer.models import PerformerItem
from rsac_relatorios_risco.performer.queue_selector import (
    filter_eligible_items,
    is_item_eligible,
)


def test_is_item_eligible_accepts_pending_and_retryable_error_statuses():
    assert is_item_eligible("pendente", 0, 3) is True
    assert is_item_eligible("erro sistêmico", 1, 3) is True
    assert is_item_eligible("exceção negocial", 2, 3) is True


def test_is_item_eligible_rejects_success_and_processing_or_max_attempts_reached():
    assert is_item_eligible("sucesso", 0, 3) is False
    assert is_item_eligible("processando", 1, 3) is False
    assert is_item_eligible("erro sistêmico", 3, 3) is False


def test_filter_eligible_items_returns_only_processable_items():
    items = [
        PerformerItem(item_id=1, reference="A", status="pendente", attempts=[]),
        PerformerItem(item_id=2, reference="B", status="sucesso", attempts=[]),
        PerformerItem(item_id=3, reference="C", status="erro sistêmico", attempts=[{}, {}]),
    ]

    eligible = filter_eligible_items(items, max_attempts=3)

    assert [item.item_id for item in eligible] == [1, 3]
