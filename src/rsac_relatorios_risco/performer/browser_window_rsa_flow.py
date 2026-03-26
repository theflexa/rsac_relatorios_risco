from __future__ import annotations

from pathlib import Path

from rsac_relatorios_risco.web.browser_window_flow import BrowserWindowPortalFlow


class BrowserWindowPerformerRsaFlow:
    def __init__(self, *, flow_factory=None) -> None:
        self.flow_factory = flow_factory or (
            lambda browser_window: BrowserWindowPortalFlow(browser_window=browser_window)
        )
        self._browser_window = None
        self._portal_flow = None
        self._competencia: str | None = None
        self._tipo_relatorio: str | None = None
        self._cooperativa: str | None = None

    def bind_browser_window(self, browser_window) -> None:
        self._browser_window = browser_window
        self._portal_flow = self.flow_factory(browser_window)
        self._competencia = None
        self._tipo_relatorio = None
        self._cooperativa = None

    def validar_home(self) -> None:
        flow = self._require_flow()
        flow._focus_portal_tab()
        flow._ensure_form_page()

    def preencher_filtros(self, *, competencia: str, tipo_relatorio: str) -> None:
        self._require_flow()
        self._competencia = competencia
        self._tipo_relatorio = tipo_relatorio

    def selecionar_cooperativas(self, cooperativas) -> None:
        self._require_flow()
        cooperativas = list(cooperativas or [])
        if len(cooperativas) != 1:
            raise RuntimeError("Fluxo RSAC atual suporta somente uma cooperativa por execução.")
        self._cooperativa = cooperativas[0]

    def exportar_relatorio(self, download_dir: Path) -> Path:
        flow = self._require_flow()
        if not self._competencia:
            raise RuntimeError("Competência não foi informada antes da exportação.")
        if not self._cooperativa:
            raise RuntimeError("Cooperativa não foi informada antes da exportação.")
        return flow.executar_fluxo_exportacao(
            competencia=self._competencia,
            cooperativa=self._cooperativa,
            download_dir=Path(download_dir),
        )

    def _require_flow(self):
        if self._portal_flow is None:
            raise RuntimeError(
                "A janela do navegador RSAC não foi vinculada ao performer antes da navegação web.",
            )
        return self._portal_flow
