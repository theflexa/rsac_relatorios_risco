from pathlib import Path

from rsac_relatorios_risco.performer.batch_runner import PerformerBatchRunner
from rsac_relatorios_risco.services.report_service import ReportData


class FakeConsolidadoService:
    def __init__(self) -> None:
        self.applied_reports: list[tuple[Path, ReportData]] = []

    def apply_report(self, workbook_path: Path, report: ReportData) -> None:
        self.applied_reports.append((workbook_path, report))


class FakeSharepointClient:
    def __init__(self) -> None:
        self.calls: list[tuple[Path, str]] = []

    def upload_incremental(self, workbook_path: Path, destination: str) -> bool:
        self.calls.append((workbook_path, destination))
        return True


def test_publish_one_updates_workbook_and_uploads_incrementally(tmp_path: Path):
    workbook_path = tmp_path / "consolidado.xlsx"
    workbook_path.write_text("placeholder", encoding="utf-8")
    report = ReportData(
        cooperativa="3333",
        competencia="03/2026",
        headers=["Central", "Singular"],
        rows=[["1004", "3333 - SICOOB SECOVICRED"]],
        data_emissao="10/04/2026 11:05",
        criterios="DATABASE: 032026, CENTRAL: 1004, SINGULAR: 3333",
        all_rows=[
            ["SISBR - RISCOS SOCIAL, AMBIENTAL E CLIMATICO"],
            ["RELATORIO DE RISCO POR COOPERATIVA"],
            ["1004 - SICOOB NOVA CENTRAL"],
            ["DATA DE EMISSAO", "10/04/2026 11:05"],
            ["CRITERIOS", "DATABASE: 032026, CENTRAL: 1004, SINGULAR: 3333"],
            ["Central", "Singular"],
            ["1004", "3333 - SICOOB SECOVICRED"],
        ],
    )
    consolidado_service = FakeConsolidadoService()
    sharepoint_client = FakeSharepointClient()
    runner = PerformerBatchRunner(consolidado_service, sharepoint_client)

    result = runner.publish_one(
        report=report,
        workbook_path=workbook_path,
        destination="sharepoint/2026-03/consolidado.xlsx",
    )

    assert result.sheet_saved is True
    assert result.sharepoint_published is True
    assert consolidado_service.applied_reports == [(workbook_path, report)]
    assert sharepoint_client.calls == [
        (workbook_path, "sharepoint/2026-03/consolidado.xlsx"),
    ]
