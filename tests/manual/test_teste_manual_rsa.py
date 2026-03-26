from pathlib import Path

from scripts import teste_manual_rsa


class FakeLogger:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def info(self, message: str) -> None:
        self.messages.append(message)


class FakeRunner:
    def __init__(self) -> None:
        self.calls = []

    def run(self, **kwargs):
        self.calls.append(kwargs)
        return Path("temp/manual_rsa/relatorio_3333_032026.xlsx")


def test_run_with_settings_uses_explicit_top_level_variables(monkeypatch):
    fake_runner = FakeRunner()
    fake_logger = FakeLogger()

    monkeypatch.setattr(
        teste_manual_rsa,
        "build_runner",
        lambda settings, logger: fake_runner,
    )

    settings = teste_manual_rsa.ManualTestSettings(
        competencia="03/2026",
        cooperativa="3333",
        download_dir=Path("temp/manual_rsa"),
        browser="chrome",
        skip_sisbr=False,
        sisbr_exe="C:/Sisbr 2.0/Sisbr 2.0.exe",
        lib_sisbr_path=Path("C:/lib_sisbr_desktop"),
    )

    result = teste_manual_rsa.run_with_settings(settings, logger=fake_logger)

    assert result == Path("temp/manual_rsa/relatorio_3333_032026.xlsx")
    assert fake_runner.calls == [
        {
            "competencia": "03/2026",
            "cooperativa": "3333",
            "download_dir": Path("temp/manual_rsa"),
            "skip_sisbr": False,
        },
    ]
    assert fake_logger.messages == [
        "Iniciando teste manual RSA",
        f"Teste manual concluido. Arquivo salvo em: {Path('temp/manual_rsa/relatorio_3333_032026.xlsx')}",
    ]
