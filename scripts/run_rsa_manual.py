from __future__ import annotations

import argparse
from pathlib import Path
import sys

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


class _Logger:
    def info(self, message: str) -> None:
        print(f"[RSA-MANUAL] {message}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Runner manual da jornada RSA para smoke test local.",
    )
    parser.add_argument("--competencia", required=True, help="Competencia no formato MM/AAAA.")
    parser.add_argument("--cooperativa", required=True, help="Codigo da cooperativa.")
    parser.add_argument(
        "--download-dir",
        default="temp/manual_rsa",
        help="Pasta onde o arquivo final sera salvo.",
    )
    parser.add_argument(
        "--browser",
        choices=["chrome", "edge"],
        default="chrome",
        help="Navegador anexado via porta de depuracao.",
    )
    parser.add_argument(
        "--debug-port",
        type=int,
        default=9222,
        help="Porta de depuracao do navegador.",
    )
    parser.add_argument(
        "--skip-sisbr",
        action="store_true",
        help="Pula a abertura do Sisbr e assume que a pagina RSA ja esta acessivel no navegador.",
    )
    parser.add_argument(
        "--sisbr-exe",
        default=None,
        help="Caminho do Sisbr 2.0.exe. Se omitido, usa o valor padrao da lib.",
    )
    parser.add_argument(
        "--lib-sisbr-path",
        default=str(default_lib_sisbr_path()),
        help="Raiz da lib_sisbr_desktop.",
    )
    return parser


def main() -> int:
    load_dotenv()
    args = build_parser().parse_args()
    logger = _Logger()

    browser_session = DebugBrowserSession(
        browser=args.browser,
        debug_port=args.debug_port,
    )
    sisbr_session = None
    if not args.skip_sisbr:
        sisbr_session = LibSisbrDesktopSession(
            lib_path=Path(args.lib_sisbr_path),
            sisbr_exe=args.sisbr_exe,
        )

    runner = ManualRsaSmokeRunner(
        browser_session=browser_session,
        sisbr_session=sisbr_session,
        logger=logger,
    )
    output_path = runner.run(
        competencia=args.competencia,
        cooperativa=args.cooperativa,
        download_dir=Path(args.download_dir),
        skip_sisbr=args.skip_sisbr,
    )
    logger.info(f"Smoke test concluido. Arquivo salvo em: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
