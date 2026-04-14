from pathlib import Path
from types import SimpleNamespace

import pytest

from rsac_relatorios_risco.web.browser_window_flow import (
    BrowserWindowFlowError,
    BrowserWindowPortalFlow,
)


class FakeWindow:
    def __init__(self, descendants=None) -> None:
        self.focus_calls = 0
        self._descendants = list(descendants or [])

    def set_focus(self) -> None:
        self.focus_calls += 1

    def descendants(self, control_type=None):
        if control_type is None:
            return list(self._descendants)
        if control_type == "Edit":
            return [
                control
                for control in self._descendants
                if getattr(control, "friendly_class_name", lambda: "")() == "Edit"
            ]
        return []


class FakeControl:
    def __init__(
        self,
        *,
        text: str = "",
        name: str = "",
        automation_id: str = "",
        friendly_class_name: str = "Edit",
    ) -> None:
        self._text = text
        self._friendly_class_name = friendly_class_name
        self.element_info = SimpleNamespace(name=name, automation_id=automation_id)
        self.clicks = 0
        self.focus_calls = 0

    def window_text(self) -> str:
        return self._text

    def friendly_class_name(self) -> str:
        return self._friendly_class_name

    def click_input(self) -> None:
        self.clicks += 1

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

    assert result == tmp_path / "03-2026" / "1004" / "alerta_1004_032026.png"
    assert shots == [str(tmp_path / "03-2026" / "1004" / "alerta_1004_032026.png")]
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

    assert result == tmp_path / "03-2026" / "1004" / "relatorio_1004_032026.xlsx"
    assert save_as.calls == [tmp_path / "03-2026" / "1004" / "relatorio_1004_032026.xlsx"]
    assert clicked == [{"relatorio": "RELATORIO_RISCO_COOPERATIVA", "status": "Processado com sucesso"}]


def test_current_url_uses_browser_address_bar_instead_of_first_edit():
    search_input = FakeControl(text="", name="Pesquisar cooperativa")
    address_bar = FakeControl(
        text="https://portal.sisbr.coop.br/rsa/risco",
        name="Address and search bar",
    )
    window = FakeWindow(descendants=[search_input, address_bar])
    flow = BrowserWindowPortalFlow(
        browser_window=window,
        sleep=lambda _: None,
    )

    assert flow._current_url() == "https://portal.sisbr.coop.br/rsa/risco"


def test_parse_script_result_reads_marker_from_url_fragment():
    payload = BrowserWindowPortalFlow._parse_script_result(
        "https://portal.sisbr.coop.br/rsa/risco#RSAFLOW123|OK|03%2F2026",
        "RSAFLOW123",
    )

    assert payload == "03/2026"


def test_parse_script_result_raises_when_script_returns_error():
    with pytest.raises(BrowserWindowFlowError, match="timeout:menu item"):
        BrowserWindowPortalFlow._parse_script_result(
            "https://portal.sisbr.coop.br/rsa/risco#RSAFLOW123|ERR|timeout%3Amenu%20item",
            "RSAFLOW123",
        )


def test_activate_address_bar_raises_clear_error_when_browser_edit_is_missing(monkeypatch):
    window = FakeWindow(descendants=[FakeControl(text="", name="Pesquisar cooperativa")])
    flow = BrowserWindowPortalFlow(
        browser_window=window,
        sleep=lambda _: None,
    )
    monkeypatch.setattr("rsac_relatorios_risco.web.browser_window_flow.pyautogui.hotkey", lambda *args: None)

    with pytest.raises(BrowserWindowFlowError, match="barra de endereco"):
        flow._activate_address_bar()


def test_ensure_form_page_does_not_assume_path_means_form_is_ready():
    clicked: list[str] = []
    responses = iter(["/rsa/risco", "overlay-closed", "not-form", "/rsa/risco", "overlay-closed"])
    flow = BrowserWindowPortalFlow(
        browser_window=FakeWindow(),
        sleep=lambda _: None,
    )
    flow._run_script = lambda body, **kwargs: next(responses)
    flow._click_dom_target = lambda locator_script, **kwargs: clicked.append(locator_script)
    flow._wait_for_template = lambda *args, **kwargs: None

    flow._ensure_form_page()

    assert len(clicked) == 2
    assert "Relat" in clicked[0]
    assert "Riscos Social" in clicked[1]


def test_ensure_form_page_closes_reports_overlay_before_using_form():
    clicked: list[str] = []
    run_calls: list[str] = []
    responses = iter(
        [
            "/rsa/risco",
            "overlay-open",
            "overlay-closed",
            "form-ready",
        ]
    )
    flow = BrowserWindowPortalFlow(
        browser_window=FakeWindow(),
        sleep=lambda _: None,
    )

    def fake_run_script(body, **kwargs):
        run_calls.append(body)
        return next(responses)

    flow._run_script = fake_run_script
    flow._click_dom_target = lambda locator_script, **kwargs: clicked.append(locator_script)

    flow._ensure_form_page()

    assert len(clicked) == 1
    assert "Relat" not in clicked[0]
    assert "relatorios disponiveis" in clicked[0].casefold()
    assert len(run_calls) == 4


def test_fill_form_waits_for_dropdown_options_before_clicking():
    locators: list[str] = []
    flow = BrowserWindowPortalFlow(
        browser_window=FakeWindow(),
        sleep=lambda _: None,
    )
    flow._click_dom_target = lambda locator_script, **kwargs: locators.append(locator_script)
    flow._run_script = lambda body, **kwargs: "03/2026"

    flow._fill_form(competencia="03/2026", cooperativa="3042")

    assert "const wait = async" in locators[1]
    assert "Relat\\u00f3rio por Cooperativa" in locators[1]
    assert "const wait = async" in locators[3]
    assert '3042 -' in locators[3]
