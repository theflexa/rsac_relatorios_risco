from __future__ import annotations

import os
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
    BrowserWindowSession,
    LibSisbrDesktopSession,
    ManualRsaSmokeRunner,
    default_lib_sisbr_path,
)
from rsac_relatorios_risco.web.browser_window_flow import BrowserWindowPortalFlow
from utils.rpa_actions import kill_all_processes


@dataclass(slots=True)
class ManualTestSettings:
    competencia: str
    cooperativa: str
    download_dir: Path
    browser: str
    skip_sisbr: bool
    sisbr_exe: str | None
    lib_sisbr_path: Path
    # Etapas pos-download
    skip_consolidado: bool
    skip_sharepoint: bool
    skip_email: bool
    template_path: Path
    consolidado_dir: Path


class _Logger:
    def info(self, message: str) -> None:
        print(f"[TESTE-MANUAL-RSA] {message}")


# ============================================================
# VARIAVEIS ESSENCIAIS DO TESTE MANUAL
# Altere somente estes valores e aperte Run.
# IMPORTANTE: este script precisa rodar na sessao normal do Windows.
# Execucao sandboxed/virtualizada pode disparar falso erro de conectividade
# no Sisbr ou fazer o OCR/click acertar outra janela no login.
# ============================================================
load_dotenv()

COMPETENCIA = "04/2026"
COOPERATIVA = "3042"
DOWNLOAD_DIR = PROJECT_ROOT / "temp" / "manual_rsa"
BROWSER = "chrome"
SKIP_SISBR = False
SISBR_EXE = None
LIB_SISBR_PATH = default_lib_sisbr_path()

# Etapas pos-download (14-18)
SKIP_CONSOLIDADO = False
SKIP_SHAREPOINT = False       # True por padrao — requer credenciais reais
SKIP_EMAIL = False             # True por padrao — requer credenciais reais
TEMPLATE_PATH = PROJECT_ROOT / "Models" / "Modelo_PlanilhaPrincipal.xlsx"
CONSOLIDADO_DIR = PROJECT_ROOT / "temp" / "manual_rsa" / "consolidado"


def current_settings() -> ManualTestSettings:
    return ManualTestSettings(
        competencia=COMPETENCIA,
        cooperativa=COOPERATIVA,
        download_dir=Path(DOWNLOAD_DIR),
        browser=BROWSER,
        skip_sisbr=SKIP_SISBR,
        sisbr_exe=SISBR_EXE,
        lib_sisbr_path=Path(LIB_SISBR_PATH),
        skip_consolidado=SKIP_CONSOLIDADO,
        skip_sharepoint=SKIP_SHAREPOINT,
        skip_email=SKIP_EMAIL,
        template_path=Path(TEMPLATE_PATH),
        consolidado_dir=Path(CONSOLIDADO_DIR),
    )


def build_runner(settings: ManualTestSettings, logger: _Logger) -> ManualRsaSmokeRunner:
    browser_session = BrowserWindowSession(
        browser=settings.browser,
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
        rsa_flow_factory=lambda browser_window: BrowserWindowPortalFlow(browser_window=browser_window),
    )


def run_with_settings(settings: ManualTestSettings, logger=None) -> Path:
    logger = logger or _Logger()

    # --- Etapas 1-13: Sisbr -> portal RSA -> download ---
    logger.info("Iniciando teste manual RSA")
    runner = build_runner(settings, logger)
    output_path = runner.run(
        competencia=settings.competencia,
        cooperativa=settings.cooperativa,
        download_dir=settings.download_dir,
        skip_sisbr=settings.skip_sisbr,
    )
    logger.info(f"Teste manual concluido. Arquivo salvo em: {output_path}")

    # --- Etapa 14: Ler relatorio exportado ---
    from rsac_relatorios_risco.services.report_service import read_report

    logger.info(f"Lendo relatorio exportado: {output_path}")
    report = read_report(output_path)
    logger.info(
        f"Relatorio lido: cooperativa={report.cooperativa} "
        f"competencia={report.competencia} "
        f"linhas={len(report.rows)}"
    )

    # --- Etapas 15-16: Preencher consolidado ---
    if not settings.skip_consolidado:
        from rsac_relatorios_risco.services.consolidado_service import apply_report
        from rsac_relatorios_risco.performer.consolidado_resolver import resolve_monthly_workbook

        file_name = f"RSAC_{settings.competencia.replace('/', '')}.xlsx"
        workbook_path = resolve_monthly_workbook(
            template_path=settings.template_path,
            output_dir=settings.consolidado_dir,
            competencia=settings.competencia,
            file_name=file_name,
        )
        logger.info(f"Consolidado resolvido: {workbook_path}")

        apply_report(workbook_path, report)
        logger.info(f"Aba da cooperativa {report.cooperativa} preenchida no consolidado")
    else:
        logger.info("Consolidado pulado (SKIP_CONSOLIDADO=True)")

    # --- Etapa 17: Upload SharePoint ---
    if not settings.skip_sharepoint:
        from utils.sharepoint import upload_file as sharepoint_upload, build_rsac_folder_path, build_rsac_month_folder_path

        sp_site_url = os.getenv("SHAREPOINT_SITE_URL", "")
        sp_biblioteca = os.getenv("SHAREPOINT_BIBLIOTECA", "Documentos Compartilhados")
        sp_base_folder = os.getenv("SHAREPOINT_FOLDER_PATH", "")
        sp_creds = {
            "tenant_id": os.getenv("SHAREPOINT_TENANT_ID", ""),
            "client_id": os.getenv("SHAREPOINT_CLIENT_ID", ""),
            "client_secret": os.getenv("SHAREPOINT_CLIENT_SECRET", ""),
        }
        if not sp_site_url:
            logger.info("SHAREPOINT_SITE_URL nao configurado, pulando upload")
        else:
            # 17a. Upload insumo (pasta da cooperativa)
            insumo_folder = build_rsac_folder_path(
                sp_base_folder,
                competencia=settings.competencia,
                cooperativa=settings.cooperativa,
            )
            logger.info(f"Enviando insumo para SharePoint: {sp_biblioteca}/{insumo_folder}")
            sharepoint_upload(
                output_path,
                site_url=sp_site_url,
                folder_path=insumo_folder,
                biblioteca=sp_biblioteca,
                **sp_creds,
            )
            logger.info("Upload insumo concluido")

            # 17b. Upload consolidado (pasta do mês)
            consolidado_folder = build_rsac_month_folder_path(
                sp_base_folder,
                competencia=settings.competencia,
            )
            logger.info(f"Enviando consolidado para SharePoint: {sp_biblioteca}/{consolidado_folder}")
            web_url = sharepoint_upload(
                workbook_path,
                site_url=sp_site_url,
                folder_path=consolidado_folder,
                biblioteca=sp_biblioteca,
                **sp_creds,
            )
            logger.info(f"Upload consolidado concluido: {web_url}")
    else:
        logger.info("SharePoint pulado (SKIP_SHAREPOINT=True)")

    # --- Etapa 18: Envio de e-mail ---
    if not settings.skip_email:
        from rsac_relatorios_risco.services.email_service import send_summary

        mail_from = os.getenv("MAIL_FROM") or os.getenv("FROM_EMAIL", "")
        if not mail_from:
            logger.info("MAIL_FROM/FROM_EMAIL nao configurado, pulando e-mail")
        else:
            summary = {
                "concluidos": [settings.cooperativa],
                "erros_sistemicos": [],
            }
            logger.info(f"Enviando e-mail de resumo de {mail_from}")
            send_summary(
                summary,
                settings={"MailDestinatarioResultado": "sergio.oliveira@sicoobnovacentral.com.br"},
                competencia=settings.competencia,
                mail_from=mail_from,
                tenant_id=os.getenv("EMAIL_TENANT_ID") or os.getenv("SHAREPOINT_TENANT_ID", ""),
                client_id=os.getenv("EMAIL_CLIENT_ID") or os.getenv("SHAREPOINT_CLIENT_ID", ""),
                client_secret=os.getenv("EMAIL_CLIENT_SECRET") or os.getenv("SHAREPOINT_CLIENT_SECRET", ""),
            )
            logger.info("E-mail enviado com sucesso")
    else:
        logger.info("E-mail pulado (SKIP_EMAIL=True)")

    return output_path


def main() -> int:
    kill_all_processes()
    try:
        run_with_settings(current_settings())
        return 0
    except Exception:
        raise
    finally:
        kill_all_processes()


if __name__ == "__main__":
    raise SystemExit(main())
