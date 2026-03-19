from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_PATH = PROJECT_ROOT / "src"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from rsac_relatorios_risco.manual.rsa_smoke_runner import (
    DebugBrowserSession,
    LibSisbrDesktopSession,
    ManualRsaSmokeRunner,
    default_lib_sisbr_path,
)


@dataclass(slots=True)
class ManualTestSettings:
    competencia: str
    cooperativa: str
    download_dir: Path
    browser: str
    debug_port: int
    skip_sisbr: bool
    sisbr_exe: str | None
    lib_sisbr_path: Path


class _Logger:
    def info(self, message: str) -> None:
        print(f"[TESTE-MANUAL-RSA] {message}")


# ============================================================
# VARIAVEIS ESSENCIAIS DO TESTE MANUAL
# Altere somente estes valores e aperte Run.
# ============================================================
COMPETENCIA = "03/2026"
COOPERATIVA = "3333"
DOWNLOAD_DIR = PROJECT_ROOT / "temp" / "manual_rsa"
BROWSER = "chrome"
DEBUG_PORT = 9222
SKIP_SISBR = False
SISBR_EXE = None
LIB_SISBR_PATH = default_lib_sisbr_path()


def current_settings() -> ManualTestSettings:
    return ManualTestSettings(
        competencia=COMPETENCIA,
        cooperativa=COOPERATIVA,
        download_dir=Path(DOWNLOAD_DIR),
        browser=BROWSER,
        debug_port=DEBUG_PORT,
        skip_sisbr=SKIP_SISBR,
        sisbr_exe=SISBR_EXE,
        lib_sisbr_path=Path(LIB_SISBR_PATH),
    )


def build_runner(settings: ManualTestSettings, logger: _Logger) -> ManualRsaSmokeRunner:
    browser_session = DebugBrowserSession(
        browser=settings.browser,
        debug_port=settings.debug_port,
    )
    sisbr_session = None
    if not settings.skip_sisbr:
        sisbr_session = LibSisbrDesktopSession(
            lib_path=settings.lib_sisbr_path,
            sisbr_exe=settings.sisbr_exe,
        )
    return ManualRsaSmokeRunner(
        browser_session=browser_session,
        sisbr_session=sisbr_session,
        logger=logger,
    )


def run_with_settings(settings: ManualTestSettings, logger=None) -> Path:
    logger = logger or _Logger()
    logger.info("Iniciando teste manual RSA")
    runner = build_runner(settings, logger)
    output_path = runner.run(
        competencia=settings.competencia,
        cooperativa=settings.cooperativa,
        download_dir=settings.download_dir,
        skip_sisbr=settings.skip_sisbr,
    )
    logger.info(f"Teste manual concluido. Arquivo salvo em: {output_path}")
    return output_path


def main() -> int:
    load_dotenv()
    run_with_settings(current_settings())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
