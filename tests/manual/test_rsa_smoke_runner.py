from pathlib import Path

from rsac_relatorios_risco.manual.rsa_smoke_runner import (
    BrowserWindowSession,
    ManualRsaSmokeRunner,
)


class FakeLogger:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def info(self, message: str) -> None:
        self.messages.append(message)


class FakeSisbrSession:
    def __init__(self) -> None:
        self.calls = 0

    def ensure_rsa_open(self):
        self.calls += 1
        return "janela-rsa"


class FakeBrowserSession:
    def __init__(self) -> None:
        self.calls = 0
        self.close_calls = 0
        self.prepare_calls = 0
        self.received_windows = []

    def close_preexisting_tabs(self):
        self.close_calls += 1

    def prepare_for_external_navigation(self):
        self.prepare_calls += 1

    def attach(self, browser_window=None):
        self.calls += 1
        self.received_windows.append(browser_window)
        return object()


class FakeFlow:
    def __init__(self, driver, output_path: Path) -> None:
        self.driver = driver
        self.output_path = output_path
        self.calls = []

    def executar_fluxo_exportacao(self, *, competencia, cooperativa, download_dir):
        self.calls.append((competencia, cooperativa, download_dir))
        return self.output_path


def test_manual_runner_executes_sisbr_attach_and_rsa_flow(tmp_path: Path):
    logger = FakeLogger()
    sisbr = FakeSisbrSession()
    browser = FakeBrowserSession()
    expected = tmp_path / "relatorio_3333_032026.xlsx"
    captured = {}

    def factory(driver):
        flow = FakeFlow(driver, expected)
        captured["flow"] = flow
        return flow

    runner = ManualRsaSmokeRunner(
        browser_session=browser,
        sisbr_session=sisbr,
        logger=logger,
        rsa_flow_factory=factory,
    )

    result = runner.run(
        competencia="03/2026",
        cooperativa="3333",
        download_dir=tmp_path,
    )

    assert result == expected
    assert sisbr.calls == 1
    assert browser.close_calls == 1
    assert browser.prepare_calls == 1
    assert browser.calls == 1
    assert browser.received_windows == ["janela-rsa"]
    assert captured["flow"].calls == [("03/2026", "3333", tmp_path)]
    assert logger.messages == [
        "Fechando abas preexistentes do navegador",
        "Preparando navegador para receber o portal do Sisbr",
        "Abrindo Sisbr, garantindo login e acessando modulo RSA",
        "Conectando a janela do navegador aberta pelo Sisbr",
        "Executando jornada RSA completa",
        f"Arquivo gerado em {expected}",
    ]


def test_manual_runner_can_skip_sisbr(tmp_path: Path):
    logger = FakeLogger()
    sisbr = FakeSisbrSession()
    browser = FakeBrowserSession()
    expected = tmp_path / "relatorio_3333_032026.xlsx"

    runner = ManualRsaSmokeRunner(
        browser_session=browser,
        sisbr_session=sisbr,
        logger=logger,
        rsa_flow_factory=lambda driver: FakeFlow(driver, expected),
    )

    runner.run(
        competencia="03/2026",
        cooperativa="3333",
        download_dir=tmp_path,
        skip_sisbr=True,
    )

    assert sisbr.calls == 0
    assert browser.close_calls == 0
    assert browser.prepare_calls == 0
    assert browser.received_windows == [None]


def test_browser_window_session_reuses_window_from_sisbr():
    session = BrowserWindowSession(
        browser="chrome",
    )

    result = session.attach(browser_window="janela-rsa")

    assert result == "janela-rsa"
