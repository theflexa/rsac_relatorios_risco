from pathlib import Path

from rsac_relatorios_risco.performer.item_runner import PerformerItemRunner
from rsac_relatorios_risco.performer.models import PerformerItem


class FakeSisbrFlow:
    def __init__(self) -> None:
        self.calls = []

    def acessar_modulo_rsa(self):
        self.calls.append("acessar_modulo_rsa")
        return "janela-rsa"


class FakeFlow:
    def __init__(self) -> None:
        self.calls = []
        self.bound_windows = []

    def bind_browser_window(self, browser_window):
        self.bound_windows.append(browser_window)

    def validar_home(self):
        self.calls.append("validar_home")

    def preencher_filtros(self, *, competencia, tipo_relatorio):
        self.calls.append(("filtros", competencia, tipo_relatorio))

    def selecionar_cooperativas(self, cooperativas):
        self.calls.append(("coops", cooperativas))

    def exportar_relatorio(self, download_dir):
        self.calls.append(("exportar", download_dir))
        return download_dir / "relatorio.xlsx"


class FakeReportService:
    def read_report(self, path):
        return "REPORT"


class FakeBatchRunner:
    def publish_one(self, *, report, workbook_path, destination):
        return type(
            "Result",
            (),
            {"sheet_saved": True, "sharepoint_published": True},
        )()


def test_item_runner_executes_flow_for_single_item(tmp_path: Path):
    item = PerformerItem(
        item_id=1,
        reference="3333_RSAC_RISCO_032026",
        status="processando",
        attempts=[
            {
                "status": "processando",
                "attempt_number": 1,
                "started_at": "x",
                "finished_at": "",
            },
        ],
        data={
            "cooperativa": "3333",
            "competencia": "03/2026",
            "tipo_relatorio": "RSAC",
            "sharepoint": "destino",
        },
    )
    sisbr_flow = FakeSisbrFlow()
    rsa_flow = FakeFlow()
    runner = PerformerItemRunner(
        sisbr_flow=sisbr_flow,
        rsa_flow=rsa_flow,
        report_service=FakeReportService(),
        batch_runner=FakeBatchRunner(),
    )

    result = runner.run(
        item=item,
        workbook_path=tmp_path / "consolidado.xlsx",
        download_dir=tmp_path,
    )

    assert result.final_status == "sucesso"
    assert result.report_path.name == "relatorio.xlsx"
    assert sisbr_flow.calls == ["acessar_modulo_rsa"]
    assert rsa_flow.bound_windows == ["janela-rsa"]
    assert rsa_flow.calls[0] == "validar_home"
