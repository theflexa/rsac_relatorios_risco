from pathlib import Path

from rsac_relatorios_risco.performer.models import PerformerItem
from rsac_relatorios_risco.performer.orchestrator import PerformerOrchestrator


class FakeQueueRepository:
    def __init__(self, items):
        self.items = items

    def list_items(self):
        return self.items


class FakeItemUpdater:
    def __init__(self):
        self.transitions = []

    def mark_processing(self, item):
        self.transitions.append(("processando", item.item_id))
        return item

    def mark_finished(self, item, final_status):
        self.transitions.append((final_status, item.item_id))


class FakeResolver:
    def resolve(self, item):
        return Path("temp/RSAC_032026.xlsx")


class FakeRunner:
    def run(self, *, item, workbook_path, download_dir):
        return type(
            "Result",
            (),
            {"final_status": "sucesso", "report_path": download_dir / "r.xlsx"},
        )()


class FakeEmailService:
    def __init__(self):
        self.sent = None

    def send_summary(self, summary):
        self.sent = summary


def test_orchestrator_processes_only_eligible_items_until_queue_is_exhausted(
    tmp_path: Path,
):
    items = [
        PerformerItem(
            item_id=1,
            reference="A",
            status="pendente",
            attempts=[],
            data={"competencia": "03/2026"},
        ),
        PerformerItem(
            item_id=2,
            reference="B",
            status="sucesso",
            attempts=[],
            data={"competencia": "03/2026"},
        ),
    ]
    email_service = FakeEmailService()
    orchestrator = PerformerOrchestrator(
        queue_repository=FakeQueueRepository(items),
        item_updater=FakeItemUpdater(),
        consolidado_resolver=FakeResolver(),
        item_runner=FakeRunner(),
        email_service=email_service,
        max_attempts=3,
        download_dir=tmp_path,
    )

    summary = orchestrator.run()

    assert summary["concluidos"] == ["A"]
    assert summary["ignorados_por_max_attempts"] == []
    assert email_service.sent == summary
