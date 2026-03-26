from scripts import teste_manual_rsa
from rsac_relatorios_risco.manual.rsa_smoke_runner import BrowserWindowSession


class FakeLogger:
    def info(self, message: str) -> None:
        del message


def test_build_runner_reuses_browser_window_opened_by_sisbr():
    settings = teste_manual_rsa.ManualTestSettings(
        competencia="03/2026",
        cooperativa="3042",
        download_dir=teste_manual_rsa.PROJECT_ROOT / "temp" / "manual_rsa",
        browser="chrome",
        skip_sisbr=True,
        sisbr_exe=None,
        lib_sisbr_path=teste_manual_rsa.default_lib_sisbr_path(),
    )

    runner = teste_manual_rsa.build_runner(settings, FakeLogger())

    assert isinstance(runner.browser_session, BrowserWindowSession)
    flow = runner.rsa_flow_factory(browser_window=object())
    assert flow.__class__.__name__ == "BrowserWindowPortalFlow"
