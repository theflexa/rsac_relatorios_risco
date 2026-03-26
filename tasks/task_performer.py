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
  6. Atualiza status no banco (sucesso / erro sistêmico)
  7. kill_all_processes (cleanup final)
"""
from __future__ import annotations

import sys
import traceback
from pathlib import Path

from jarbis_external_client.model import ExternalTask, TaskResult
from loguru import logger

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from utils.database import get_item_by_id, has_database_config, update_item, update_item_merge
from utils.rpa_actions import kill_all_processes

from rsac_relatorios_risco.manual.rsa_smoke_runner import (
    BrowserWindowSession,
    ManualRsaSmokeRunner,
    default_lib_sisbr_path,
)
from rsac_relatorios_risco.sisbr.desktop_session import LibSisbrDesktopSession
from rsac_relatorios_risco.web.browser_window_flow import BrowserWindowPortalFlow


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOWNLOAD_DIR = PROJECT_ROOT / "temp" / "downloads"


def _utc_now_z() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def task_performer(task: ExternalTask) -> TaskResult:
    logger.info("Iniciando Performer - Task ID: {}", task.task_id)

    if not has_database_config():
        return task.failure(
            error_message="Config do banco ausente",
            error_details="Defina DATABASE_URL e DATABASE_API_KEY no .env.",
        )

    item_id = task.get_variable("item_id")
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

    try:
        # 1. Buscar item no banco
        item = get_item_by_id(item_id_int)
        if not item:
            raise RuntimeError(f"Item não encontrado no banco: item_id={item_id_int}")

        data = item.get("data", {})
        cooperativa = data.get("cooperativa", "")
        competencia = data.get("competencia", "")
        reference = item.get("reference", "")

        logger.info(
            "Processando item_id={} cooperativa={} competencia={} reference={}",
            item_id_int, cooperativa, competencia, reference,
        )

        # 2. Marcar como processando
        update_item(item_id_int, status="processando")

        # 3. Cleanup inicial
        kill_all_processes()

        # 4. Executar fluxo RSA
        output_path = _executar_fluxo_rsa(
            cooperativa=cooperativa,
            competencia=competencia,
            download_dir=DOWNLOAD_DIR,
        )

        # 5. Confirmar download
        if not output_path.exists():
            raise RuntimeError(f"Download falhou: arquivo não encontrado em {output_path}")

        # 6. Sucesso
        update_item_merge(
            item_id_int,
            status="sucesso",
            data={
                "resultado": {
                    "concluido_em": _utc_now_z(),
                    "arquivo": str(output_path),
                }
            },
        )

        logger.success(
            "Item processado com sucesso. item_id={} cooperativa={} arquivo={}",
            item_id_int, cooperativa, output_path,
        )

        return task.complete(
            variables={
                "item_id": item_id_int,
                "cooperativa": cooperativa,
                "arquivo": str(output_path),
            }
        )

    except Exception as exc:
        logger.exception("Falha ao processar item_id={}", item_id_int)
        try:
            update_item_merge(
                item_id_int,
                status="erro sistêmico",
                data={"error": {"at": _utc_now_z(), "message": str(exc)}},
            )
        except Exception:
            logger.exception("Falha ao atualizar status de erro no banco. item_id={}", item_id_int)

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
