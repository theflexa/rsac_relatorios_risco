from pathlib import Path

from rsac_relatorios_risco.performer.models import PerformerItem
from rsac_relatorios_risco.performer.run_performer import StepByStepPerformer


class FakeLogger:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def info(self, message: str) -> None:
        self.messages.append(message)


class FakeQueueRepository:
    def __init__(self, items):
        self.items = items

    def list_items(self):
        return self.items


class FakeItemUpdater:
    def __init__(self) -> None:
        self.transitions = []

    def mark_processing(self, item):
        self.transitions.append(("processando", item.item_id))
        return item

    def mark_finished(self, item, final_status):
        self.transitions.append((final_status, item.item_id))


class FakeResolver:
    def resolve(self, item):
        return Path("temp/RSAC_032026.xlsx")


class FakeRsaFlow:
    def __init__(self) -> None:
        self.calls = []

    def abrir_modulo_rsa(self):
        self.calls.append("abrir_modulo_rsa")

    def preencher_filtros(self, *, competencia, tipo_relatorio):
        self.calls.append(("preencher_filtros", competencia, tipo_relatorio))

    def selecionar_cooperativas(self, cooperativas):
        self.calls.append(("selecionar_cooperativas", cooperativas))

    def exportar_relatorio(self, download_dir):
        self.calls.append(("exportar_relatorio", download_dir))
        return download_dir / "relatorio_3333.xlsx"


class FakeReportService:
    def read_report(self, path):
        return {"cooperativa": "3333", "path": str(path)}


class FakeBatchRunner:
    def __init__(self) -> None:
        self.calls = []

    def publish_one(self, *, report, workbook_path, destination):
        self.calls.append((report, workbook_path, destination))
        return type(
            "Result",
            (),
            {"sheet_saved": True, "sharepoint_published": True},
        )()


class FakeEmailService:
    def __init__(self) -> None:
        self.summary = None

    def send_summary(self, summary):
        self.summary = summary


class FakeCleanupService:
    def __init__(self) -> None:
        self.calls = []

    def delete_files_older_than(self, base_dir, days):
        self.calls.append((base_dir, days))
        return []


def test_step_by_step_performer_runs_linear_flow_with_clear_logs(tmp_path: Path):
    item = PerformerItem(
        item_id=1,
        reference="3333_RSAC_RISCO_032026",
        status="pendente",
        attempts=[],
        data={
            "cooperativa": "3333",
            "competencia": "03/2026",
            "tipo_relatorio": "RSAC",
            "sharepoint": "sharepoint/RSAC_032026.xlsx",
        },
    )
    logger = FakeLogger()
    email_service = FakeEmailService()
    runner = StepByStepPerformer(
        queue_repository=FakeQueueRepository([item]),
        item_updater=FakeItemUpdater(),
        consolidado_resolver=FakeResolver(),
        rsa_flow=FakeRsaFlow(),
        report_service=FakeReportService(),
        batch_runner=FakeBatchRunner(),
        email_service=email_service,
        cleanup_service=FakeCleanupService(),
        max_attempts=3,
        download_dir=tmp_path,
        cleanup_days=15,
        logger=logger,
    )

    summary = runner.run()

    assert summary["concluidos"] == ["3333_RSAC_RISCO_032026"]
    assert email_service.summary == summary
    assert logger.messages == [
        "Iniciando execução do Performer",
        "Coletando itens elegíveis",
        "Localizando ou criando consolidado mensal",
        "Coletando item 1 - 3333_RSAC_RISCO_032026",
        "Marcando item 1 como processando",
        "Abrindo módulo RSA",
        "Preenchendo filtros da competência 03/2026",
        "Selecionando cooperativa 3333",
        "Exportando relatório da cooperativa 3333",
        "Lendo relatório exportado",
        "Atualizando aba da cooperativa 3333 e publicando consolidado",
        "Marcando item 1 como sucesso",
        "Executando limpeza de temporários antigos",
        "Enviando e-mail final",
    ]
