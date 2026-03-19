from pathlib import Path

from rsac_relatorios_risco.manual.rsa_smoke_runner import (
    DebugBrowserSession,
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

    def attach(self):
        self.calls += 1
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
    assert browser.calls == 1
    assert captured["flow"].calls == [("03/2026", "3333", tmp_path)]
    assert logger.messages == [
        "Abrindo Sisbr, garantindo login e acessando modulo RSA",
        "Anexando ao navegador com porta de depuracao",
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


def test_debug_browser_session_sets_debugger_address():
    created = {}

    class FakeOptions:
        debugger_address = None

    def fake_options_factory(browser):
        created["browser"] = browser
        return FakeOptions()

    def fake_driver_factory(browser, options):
        created["driver"] = (browser, options.debugger_address)
        return "driver"

    session = DebugBrowserSession(
        browser="chrome",
        debug_port=9333,
        options_factory=fake_options_factory,
        driver_factory=fake_driver_factory,
    )

    result = session.attach()

    assert result == "driver"
    assert created == {
        "browser": "chrome",
        "driver": ("chrome", "127.0.0.1:9333"),
    }
