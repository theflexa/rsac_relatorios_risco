from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class ItemRunResult:
    final_status: str
    report_path: Path


class PerformerItemRunner:
    def __init__(self, sisbr_flow, rsa_flow, report_service, batch_runner) -> None:
        self.sisbr_flow = sisbr_flow
        self.rsa_flow = rsa_flow
        self.report_service = report_service
        self.batch_runner = batch_runner

    def run(self, *, item, workbook_path: Path, download_dir: Path) -> ItemRunResult:
        data = item.data
        browser_window = self.sisbr_flow.acessar_modulo_rsa()
        if hasattr(self.rsa_flow, "bind_browser_window"):
            self.rsa_flow.bind_browser_window(browser_window)
        self.rsa_flow.validar_home()
        self.rsa_flow.preencher_filtros(
            competencia=data["competencia"],
            tipo_relatorio=data["tipo_relatorio"],
        )
        self.rsa_flow.selecionar_cooperativas([data["cooperativa"]])
        report_path = self.rsa_flow.exportar_relatorio(download_dir)
        report = self.report_service.read_report(report_path)
        publish_result = self.batch_runner.publish_one(
            report=report,
            workbook_path=workbook_path,
            destination=data["sharepoint"],
        )
        final_status = (
            "sucesso"
            if publish_result.sheet_saved and publish_result.sharepoint_published
            else "erro sistêmico"
        )
        return ItemRunResult(final_status=final_status, report_path=report_path)
