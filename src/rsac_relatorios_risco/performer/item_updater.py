from copy import deepcopy
from datetime import datetime, timezone


FINAL_STATUSES = {"sucesso", "erro sistêmico", "exceção negocial"}


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def open_processing_attempt(attempts: list[dict]) -> list[dict]:
    updated = deepcopy(attempts)
    if updated and updated[-1]["status"] == "processando":
        raise ValueError("Operação inválida. Status processando já existe.")
    updated.append(
        {
            "status": "processando",
            "started_at": _utc_now(),
            "finished_at": "",
            "attempt_number": len(updated) + 1,
        },
    )
    return updated


def close_attempt(attempts: list[dict], final_status: str) -> list[dict]:
    if final_status not in FINAL_STATUSES:
        raise ValueError("Status final inválido")

    updated = deepcopy(attempts)
    if not updated or updated[-1]["status"] != "processando":
        raise ValueError("Operação inválida. Status atual diferente de processando.")

    updated[-1]["status"] = final_status
    updated[-1]["finished_at"] = _utc_now()
    return updated
