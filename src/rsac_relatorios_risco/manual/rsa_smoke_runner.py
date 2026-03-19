from __future__ import annotations

import os
from pathlib import Path

from rsac_relatorios_risco.sisbr.desktop_session import LibSisbrDesktopSession
from rsac_relatorios_risco.web.rsa_portal_flow import RsaPortalFlow

try:
    from selenium.webdriver import Chrome, Edge  # type: ignore
    from selenium.webdriver.chrome.options import Options as ChromeOptions  # type: ignore
    from selenium.webdriver.edge.options import Options as EdgeOptions  # type: ignore
except ImportError:  # pragma: no cover
    Chrome = None
    Edge = None
    ChromeOptions = None
    EdgeOptions = None


class ManualRunnerDependencyError(RuntimeError):
    pass


class _FallbackLogger:
    def info(self, message: str) -> None:
        print(message)


class DebugBrowserSession:
    def __init__(
        self,
        *,
        browser: str = "chrome",
        debug_port: int = 9222,
        driver_factory=None,
        options_factory=None,
    ) -> None:
        self.browser = browser.lower()
        self.debug_port = debug_port
        self.driver_factory = driver_factory or self._default_driver_factory
        self.options_factory = options_factory or self._default_options_factory

    def attach(self):
        options = self.options_factory(self.browser)
        options.debugger_address = f"127.0.0.1:{self.debug_port}"
        return self.driver_factory(self.browser, options)

    @staticmethod
    def _default_options_factory(browser: str):
        if browser == "chrome":
            if ChromeOptions is None:
                raise ManualRunnerDependencyError("selenium nao esta instalado para anexar ao Chrome.")
            return ChromeOptions()
        if browser == "edge":
            if EdgeOptions is None:
                raise ManualRunnerDependencyError("selenium nao esta instalado para anexar ao Edge.")
            return EdgeOptions()
        raise ValueError(f"Navegador nao suportado: {browser}")

    @staticmethod
    def _default_driver_factory(browser: str, options):
        if browser == "chrome":
            if Chrome is None:
                raise ManualRunnerDependencyError("selenium nao esta instalado para anexar ao Chrome.")
            return Chrome(options=options)
        if browser == "edge":
            if Edge is None:
                raise ManualRunnerDependencyError("selenium nao esta instalado para anexar ao Edge.")
            return Edge(options=options)
        raise ValueError(f"Navegador nao suportado: {browser}")


class ManualRsaSmokeRunner:
    def __init__(
        self,
        *,
        browser_session,
        logger=None,
        sisbr_session=None,
        rsa_flow_factory=None,
    ) -> None:
        self.browser_session = browser_session
        self.logger = logger or _FallbackLogger()
        self.sisbr_session = sisbr_session
        self.rsa_flow_factory = rsa_flow_factory or (lambda driver: RsaPortalFlow(driver=driver))

    def run(
        self,
        *,
        competencia: str,
        cooperativa: str,
        download_dir: Path,
        skip_sisbr: bool = False,
    ) -> Path:
        download_dir = Path(download_dir)
        download_dir.mkdir(parents=True, exist_ok=True)

        if not skip_sisbr and self.sisbr_session is not None:
            self.logger.info("Abrindo Sisbr, garantindo login e acessando modulo RSA")
            self.sisbr_session.ensure_rsa_open()

        self.logger.info("Anexando ao navegador com porta de depuracao")
        driver = self.browser_session.attach()
        self.logger.info("Executando jornada RSA completa")
        flow = self.rsa_flow_factory(driver)
        output_path = flow.executar_fluxo_exportacao(
            competencia=competencia,
            cooperativa=cooperativa,
            download_dir=download_dir,
        )
        self.logger.info(f"Arquivo gerado em {output_path}")
        return output_path


def default_lib_sisbr_path() -> Path:
    return Path(
        os.getenv(
            "LIB_SISBR_DESKTOP_PATH",
            r"C:\Users\Guilherme Flexa\Desktop\Projetos Sicoob\Projetos Python\analisecredito_f3\lib_sisbr_desktop",
        )
    )
