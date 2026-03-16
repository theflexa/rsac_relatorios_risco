from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

from rsac_relatorios_risco.config.workbook_loader import load_config_workbook
from rsac_relatorios_risco.integrations.database_client import build_item_payload
from rsac_relatorios_risco.integrations.jarbis_client import build_process_variables


@dataclass(slots=True)
class DispatchResult:
    inserted_count: int
    skipped_count: int
    reused_references: list[str]
    log_messages: list[str]


def dispatch_config_items(
    *,
    config_path: Path,
    mes: str,
    ano: str,
    project_id: int,
    job_id: int,
    reference_exists: Callable[[str], bool],
    insert_item: Callable[[dict, dict], object],
) -> DispatchResult:
    workbook = load_config_workbook(config_path, mes=mes, ano=ano)
    reused_references: list[str] = []
    log_messages: list[str] = []
    inserted_count = 0
    skipped_count = 0

    for item in workbook.items:
        if reference_exists(item.reference):
            skipped_count += 1
            reused_references.append(item.reference)
            log_messages.append(
                f"Item {item.reference} já existe e será reaproveitado",
            )
            continue

        payload = build_item_payload(
            project_id=project_id,
            job_id=job_id,
            reference=item.reference,
            json_data=asdict(item),
        )
        variables = build_process_variables(payload)
        insert_item(payload, variables)
        inserted_count += 1
        log_messages.append(f"Item {item.reference} criado para processamento")

    return DispatchResult(
        inserted_count=inserted_count,
        skipped_count=skipped_count,
        reused_references=reused_references,
        log_messages=log_messages,
    )
