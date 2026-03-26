from pathlib import Path

import pytest

from rsac_relatorios_risco.performer.browser_window_rsa_flow import BrowserWindowPerformerRsaFlow


class FakePortalFlow:
    def __init__(self, browser_window) -> None:
        self.browser_window = browser_window
        self.calls = []

    def _focus_portal_tab(self) -> None:
        self.calls.append("focus")

    def _ensure_form_page(self) -> None:
        self.calls.append("ensure")

    def executar_fluxo_exportacao(self, *, competencia, cooperativa, download_dir):
        self.calls.append(("export", competencia, cooperativa, Path(download_dir)))
        return Path(download_dir) / f"relatorio_{cooperativa}.xlsx"


def test_browser_window_performer_flow_reuses_bound_window_and_exports(tmp_path: Path):
    created = {}

    def factory(browser_window):
        flow = FakePortalFlow(browser_window)
        created["flow"] = flow
        return flow

    adapter = BrowserWindowPerformerRsaFlow(flow_factory=factory)

    adapter.bind_browser_window("janela-rsa")
    adapter.validar_home()
    adapter.preencher_filtros(competencia="03/2026", tipo_relatorio="RSAC")
    adapter.selecionar_cooperativas(["3042"])

    result = adapter.exportar_relatorio(tmp_path)

    assert result == tmp_path / "relatorio_3042.xlsx"
    assert created["flow"].browser_window == "janela-rsa"
    assert created["flow"].calls == [
        "focus",
        "ensure",
        ("export", "03/2026", "3042", tmp_path),
    ]


def test_browser_window_performer_flow_requires_window_before_validating():
    adapter = BrowserWindowPerformerRsaFlow(flow_factory=lambda browser_window: FakePortalFlow(browser_window))

    with pytest.raises(RuntimeError, match="janela do navegador"):
        adapter.validar_home()
