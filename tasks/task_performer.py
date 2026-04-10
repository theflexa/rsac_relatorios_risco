"""
Performer: processa 1 item (cooperativa) da fila do Jarbis.

Recebe do Jarbis:
  - item_id: ID do item no banco

Fluxo:
  1. Busca item no banco
  2. kill_all_processes (cleanup inicial)
  3. Abre Sisbr 2.0, faz login, acessa módulo RSAC
  4. Exporta relatório da cooperativa
  5. Confirma download
  6. Lê relatório exportado e extrai dados
  7. Preenche planilha principal (consolidado) na aba da cooperativa
  8. Upload consolidado para o SharePoint
  9. Envia e-mail de resultado (TO = item.Destinatarios)
  10. Atualiza status no banco (sucesso / erro sistêmico)
  11. kill_all_processes (cleanup final)
"""
from __future__ import annotations

import os
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

import pyautogui
from jarbis_external_client.model import ExternalTask, TaskResult
from loguru import logger

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from utils.database import get_item_by_id, has_database_config, update_item, update_item_merge
from utils.rpa_actions import kill_all_processes
from utils.sharepoint import upload_file as sharepoint_upload, build_rsac_folder_path

from rsac_relatorios_risco.manual.rsa_smoke_runner import (
    BrowserWindowSession,
    ManualRsaSmokeRunner,
    default_lib_sisbr_path,
)
from rsac_relatorios_risco.sisbr.desktop_session import LibSisbrDesktopSession
from rsac_relatorios_risco.web.browser_window_flow import BrowserWindowPortalFlow
from rsac_relatorios_risco.services.report_service import read_report
from rsac_relatorios_risco.services.consolidado_service import apply_report
from rsac_relatorios_risco.performer.consolidado_resolver import resolve_monthly_workbook
from rsac_relatorios_risco.services.email_service import send_result_email, send_exception_email


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOWNLOAD_DIR = PROJECT_ROOT / "temp" / "downloads"
CONSOLIDADO_DIR = PROJECT_ROOT / "temp" / "consolidado"
TEMPLATE_PATH = PROJECT_ROOT / "Models" / "Modelo_PlanilhaPrincipal.xlsx"
LOGS_DIR = PROJECT_ROOT / "logs"
EX_SCREENSHOTS_PREFIX = "RSACExportacaoRelatorioRisco_"


def _unwrap(value):
    """Extrai valor real de variavel Jarbis que pode vir como {"value": "...", "type": "String"}."""
    if isinstance(value, dict) and "value" in value:
        return _unwrap(value["value"])
    return value


def _utc_now_z() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sharepoint_credentials() -> dict[str, str]:
    return {
        "tenant_id": os.getenv("SHAREPOINT_TENANT_ID", ""),
        "client_id": os.getenv("SHAREPOINT_CLIENT_ID", ""),
        "client_secret": os.getenv("SHAREPOINT_CLIENT_SECRET", ""),
    }


def _email_credentials() -> dict[str, str]:
    return {
        "tenant_id": os.getenv("EMAIL_TENANT_ID") or os.getenv("SHAREPOINT_TENANT_ID", ""),
        "client_id": os.getenv("EMAIL_CLIENT_ID") or os.getenv("SHAREPOINT_CLIENT_ID", ""),
        "client_secret": os.getenv("EMAIL_CLIENT_SECRET") or os.getenv("SHAREPOINT_CLIENT_SECRET", ""),
    }


def _mail_from() -> str:
    return os.getenv("MAIL_FROM") or os.getenv("FROM_EMAIL", "")


def _capture_exception_screenshot(reference: str, prefix: str = EX_SCREENSHOTS_PREFIX) -> Path | None:
    """Captura screenshot da tela e salva na pasta de logs."""
    try:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}{reference}_{timestamp}.png"
        path = LOGS_DIR / filename
        pyautogui.screenshot(str(path))
        logger.info("Screenshot de exceção salvo em: {}", path)
        return path
    except Exception as exc:
        logger.warning("Falha ao capturar screenshot de exceção: {}", exc)
        return None


def task_performer(task: ExternalTask) -> TaskResult:
    logger.info("Iniciando Performer - Task ID: {}", task.task_id)

    if not has_database_config():
        return task.failure(
            error_message="Config do banco ausente",
            error_details="Defina DATABASE_URL e DATABASE_API_KEY no .env.",
        )

    item_id = _unwrap(task.get_variable("item_id"))
    if item_id is None:
        return task.failure(
            error_message="Variável obrigatória ausente: item_id",
            error_details="O Performer precisa receber o item_id via variáveis do processo.",
        )

    try:
        item_id_int = int(item_id)
    except Exception:
        return task.failure(
            error_message="Variável inválida: item_id",
            error_details=f"item_id não é um inteiro: {item_id!r}",
        )

    # Variáveis para escopo do except/finally
    reference = ""
    data: dict = {}

    try:
        # 1. Buscar item no banco
        item = get_item_by_id(item_id_int)
        if not item:
            raise RuntimeError(f"Item não encontrado no banco: item_id={item_id_int}")

        data = item.get("data", {})
        cooperativa = data.get("cooperativa", "")
        competencia = data.get("competencia", "")
        reference = item.get("reference", "")
        pa = data.get("pa", "")
        nome_cooperativa = data.get("nome_cooperativa_2", "")
        sharepoint_folder = data.get("sharepoint", "")
        nome_arquivo = data.get("nome_arquivo", "")
        destinatarios = data.get("destinatarios", "")

        logger.info(
            "Processando item_id={} cooperativa={} ({}) competencia={} PA={} reference={}",
            item_id_int, cooperativa, nome_cooperativa, competencia, pa, reference,
        )

        # 2. Marcar como processando
        update_item(item_id_int, status="processando")

        # 3. Cleanup inicial
        kill_all_processes()

        # 4. Executar fluxo RSA (etapas 1-13: Sisbr → portal → download)
        output_path = _executar_fluxo_rsa(
            cooperativa=cooperativa,
            competencia=competencia,
            pa=pa,
            download_dir=DOWNLOAD_DIR,
        )

        # 5. Confirmar download
        if not output_path.exists():
            raise RuntimeError(f"Download falhou: arquivo não encontrado em {output_path}")
        logger.info("Relatório baixado: {}", output_path)

        # 6. Ler relatório exportado (etapa 14)
        logger.info("Lendo relatório exportado")
        report = read_report(output_path)
        logger.info(
            "Relatório lido: cooperativa={} competencia={}",
            report.cooperativa, report.competencia,
        )

        # 7. Preencher consolidado (etapas 15-16)
        file_name = nome_arquivo or f"RSAC_{cooperativa}_{competencia.replace('/', '')}.xlsx"
        workbook_path = resolve_monthly_workbook(
            template_path=TEMPLATE_PATH,
            output_dir=CONSOLIDADO_DIR,
            competencia=competencia,
            file_name=file_name,
        )
        logger.info("Consolidado: {}", workbook_path)

        apply_report(workbook_path, report)
        logger.info("Aba da cooperativa {} preenchida no consolidado", cooperativa)

        # 8. Upload SharePoint (etapa 17)
        sharepoint_published = False
        sharepoint_web_url = ""
        sp_site_url = os.getenv("SHAREPOINT_SITE_URL", "")
        sp_biblioteca = os.getenv("SHAREPOINT_BIBLIOTECA", "Documentos Compartilhados")
        sp_base_folder = sharepoint_folder or os.getenv("SHAREPOINT_FOLDER_PATH", "")
        if sp_site_url and sp_base_folder:
            full_folder = build_rsac_folder_path(
                sp_base_folder,
                competencia=competencia,
                cooperativa=cooperativa,
            )
            logger.info("Enviando consolidado para SharePoint: {}/{}", sp_biblioteca, full_folder)
            try:
                sharepoint_web_url = sharepoint_upload(
                    workbook_path,
                    site_url=sp_site_url,
                    folder_path=full_folder,
                    biblioteca=sp_biblioteca,
                    **_sharepoint_credentials(),
                )
                sharepoint_published = True
                logger.info("Upload SharePoint concluído: {}", sharepoint_web_url)
            except Exception as exc:
                logger.error("Falha no upload SharePoint: {}", exc)

        # 9. Sucesso
        update_item_merge(
            item_id_int,
            status="sucesso",
            data={
                "resultado": {
                    "concluido_em": _utc_now_z(),
                    "arquivo": str(output_path),
                    "consolidado": str(workbook_path),
                    "sharepoint_published": sharepoint_published,
                    "sharepoint_url": sharepoint_web_url,
                }
            },
        )

        logger.success(
            "Item processado com sucesso. item_id={} cooperativa={} ({}) arquivo={}",
            item_id_int, cooperativa, nome_cooperativa, output_path,
        )

        # 10. E-mail de resultado é enviado pelo orquestrador após todos os itens
        #     (orchestrator.py / run_performer.py → send_summary)

        return task.complete(
            variables={
                "item_id": item_id_int,
                "cooperativa": cooperativa,
                "arquivo": str(output_path),
                "sharepoint_url": sharepoint_web_url,
            }
        )

    except Exception as exc:
        logger.exception("Falha ao processar item_id={}", item_id_int)

        # Screenshot de exceção
        _capture_exception_screenshot(reference or str(item_id_int))

        try:
            update_item_merge(
                item_id_int,
                status="erro sistêmico",
                data={"error": {"at": _utc_now_z(), "message": str(exc)}},
            )
        except Exception:
            logger.exception("Falha ao atualizar status de erro no banco. item_id={}", item_id_int)

        # E-mail de exceção — TO = Settings.MailDestinatarioResultado (fallback TI)
        if _mail_from():
            try:
                send_exception_email(
                    error_message=str(exc),
                    reference=reference or str(item_id_int),
                    settings=data.get("_settings", {}),
                    competencia=data.get("competencia", ""),
                    mail_from=_mail_from(),
                    **_email_credentials(),
                )
            except Exception:
                logger.warning("Falha ao enviar e-mail de exceção")

        return task.failure(
            error_message=str(exc),
            error_details=traceback.format_exc(),
        )

    finally:
        kill_all_processes()


def _executar_fluxo_rsa(
    *,
    cooperativa: str,
    competencia: str,
    pa: str = "",
    download_dir: Path,
) -> Path:
    """Executa o fluxo completo: Sisbr → portal RSA → exportar → salvar."""
    download_dir.mkdir(parents=True, exist_ok=True)

    # Verifica se já existe
    competencia_clean = competencia.replace("/", "")
    expected_path = download_dir / f"relatorio_{cooperativa}_{competencia_clean}.xlsx"
    if expected_path.exists():
        logger.info("Relatório já existe: {}", expected_path)
        return expected_path

    browser_session = BrowserWindowSession(browser="chrome")
    sisbr_session = LibSisbrDesktopSession(
        lib_path=default_lib_sisbr_path(),
        # TODO: passar PA para o login do Sisbr quando a lib_sisbr_desktop suportar.
        # Atualmente o campo PA/NPAC está comentado no login.py da lib.
        # O PA deste item é: pa={pa!r}
    )

    runner = ManualRsaSmokeRunner(
        browser_session=browser_session,
        sisbr_session=sisbr_session,
        rsa_flow_factory=lambda bw: BrowserWindowPortalFlow(browser_window=bw),
    )

    return runner.run(
        competencia=competencia,
        cooperativa=cooperativa,
        download_dir=download_dir,
    )
