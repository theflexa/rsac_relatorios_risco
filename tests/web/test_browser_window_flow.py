from pathlib import Path

from rsac_relatorios_risco.web.browser_window_flow import BrowserWindowPortalFlow


class FakeWindow:
    def __init__(self) -> None:
        self.focus_calls = 0

    def set_focus(self) -> None:
        self.focus_calls += 1


class FakeSaveAsFlow:
    def __init__(self) -> None:
        self.calls: list[Path] = []

    def save_file(self, destination_path: Path) -> Path:
        self.calls.append(destination_path)
        return destination_path


def test_alert_status_saves_screenshot_in_output_dir(tmp_path: Path):
    shots: list[str] = []
    window = FakeWindow()
    save_as = FakeSaveAsFlow()
    flow = BrowserWindowPortalFlow(
        browser_window=window,
        save_as_flow=save_as,
        screenshot_func=lambda path: shots.append(path),
        sleep=lambda _: None,
    )

    flow._focus_portal_tab = lambda: None
    flow._ensure_form_page = lambda: None
    flow._fill_form = lambda **kwargs: None
    flow._open_export_modal = lambda: None
    flow._generate_report = lambda **kwargs: "Processado com alerta"
    flow._click_print = lambda **kwargs: (_ for _ in ()).throw(AssertionError("nao deve clicar imprimir"))

    result = flow.executar_fluxo_exportacao(
        competencia="03/2026",
        cooperativa="1004",
        download_dir=tmp_path,
    )

    assert result == tmp_path / "alerta_1004_032026.png"
    assert shots == [str(tmp_path / "alerta_1004_032026.png")]
    assert save_as.calls == []
    assert window.focus_calls == 1


def test_success_status_keeps_save_as_flow(tmp_path: Path):
    window = FakeWindow()
    save_as = FakeSaveAsFlow()
    clicked: list[dict] = []
    flow = BrowserWindowPortalFlow(
        browser_window=window,
        save_as_flow=save_as,
        screenshot_func=lambda path: None,
        sleep=lambda _: None,
    )

    flow._focus_portal_tab = lambda: None
    flow._ensure_form_page = lambda: None
    flow._fill_form = lambda **kwargs: None
    flow._open_export_modal = lambda: None
    flow._generate_report = lambda **kwargs: "Processado com sucesso"
    flow._click_print = lambda **kwargs: clicked.append(kwargs)

    result = flow.executar_fluxo_exportacao(
        competencia="03/2026",
        cooperativa="1004",
        download_dir=tmp_path,
    )

    assert result == tmp_path / "relatorio_1004_032026.xlsx"
    assert save_as.calls == [tmp_path / "relatorio_1004_032026.xlsx"]
    assert clicked == [{"relatorio": "RELATORIO_RISCO_COOPERATIVA", "status": "Processado com sucesso"}]
