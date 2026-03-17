import pytest

from rsac_relatorios_risco.performer.item_updater import (
    close_attempt,
    open_processing_attempt,
)


def test_open_processing_attempt_appends_new_processing_attempt():
    attempts = []

    updated = open_processing_attempt(attempts)

    assert updated[-1]["status"] == "processando"
    assert updated[-1]["attempt_number"] == 1
    assert updated[-1]["finished_at"] == ""


def test_open_processing_attempt_rejects_duplicate_open_processing_attempt():
    attempts = [
        {
            "status": "processando",
            "attempt_number": 1,
            "started_at": "x",
            "finished_at": "",
        },
    ]

    with pytest.raises(ValueError, match="processando já existe"):
        open_processing_attempt(attempts)


def test_close_attempt_finishes_last_processing_attempt_with_final_status():
    attempts = [
        {
            "status": "processando",
            "attempt_number": 1,
            "started_at": "x",
            "finished_at": "",
        },
    ]

    updated = close_attempt(attempts, "sucesso")

    assert updated[-1]["status"] == "sucesso"
    assert updated[-1]["finished_at"] != ""
