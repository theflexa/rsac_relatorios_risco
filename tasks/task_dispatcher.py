"""
Dispatcher: lê Config.xlsx e cria 1 item por cooperativa no banco.

Recebe do Jarbis:
  - config_path (opcional): caminho do Config.xlsx
  - mes: mês da competência (ex: "03")
  - ano: ano da competência (ex: "2026")

Retorna ao Jarbis:
  - project_id, job_id, inserted_count, skipped_count
"""
from __future__ import annotations

import os
import sys
import traceback
from dataclasses import asdict
from pathlib import Path

from jarbis_external_client.model import ExternalTask, TaskResult
from loguru import logger

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from utils.database import (
    ensure_project,
    has_database_config,
    insert_item,
    insert_job,
    reference_exists,
)
from utils.project_config import load_project_config

from rsac_relatorios_risco.config.workbook_loader import load_config_workbook


def task_dispatcher(task: ExternalTask) -> TaskResult:
    logger.info("Iniciando Dispatcher - Task ID: {}", task.task_id)

    try:
        if not has_database_config():
            return task.failure(
                error_message="Config do banco ausente",
                error_details="Defina DATABASE_URL e DATABASE_API_KEY no .env.",
            )

        # Parâmetros da competência
        mes = task.get_variable("mes") or os.getenv("RSAC_MES", "")
        ano = task.get_variable("ano") or os.getenv("RSAC_ANO", "")
        if not mes or not ano:
            return task.failure(
                error_message="Variáveis obrigatórias ausentes: mes e ano",
                error_details="O Dispatcher precisa receber mes e ano via variáveis do processo.",
            )

        config_path_str = (
            task.get_variable("config_path")
            or os.getenv("RSAC_CONFIG_PATH", "")
            or str(Path(__file__).resolve().parent.parent / "Config.xlsx")
        )
        config_path = Path(config_path_str)
        if not config_path.exists():
            return task.failure(
                error_message=f"Config.xlsx não encontrado: {config_path}",
                error_details="Verifique o caminho do arquivo de configuração.",
            )

        # Garantir projeto e job no banco
        project_config = load_project_config()
        project_id = ensure_project(project_config)
        job_id = insert_job(project_id=project_id)

        logger.info("Projeto={} Job={} criados. Lendo Config.xlsx...", project_id, job_id)

        # Ler cooperativas do Config.xlsx
        workbook = load_config_workbook(config_path, mes=mes, ano=ano)

        inserted_count = 0
        skipped_count = 0
        item_ids = []

        for config_item in workbook.items:
            if reference_exists(project_id, config_item.reference):
                skipped_count += 1
                logger.info("Item {} já existe, pulando", config_item.reference)
                continue

            item_data = asdict(config_item)
            item_data["competencia"] = f"{mes}/{ano}"

            item_id = insert_item(
                project_id=project_id,
                job_id=job_id,
                data=item_data,
                reference=config_item.reference,
            )
            item_ids.append(item_id)
            inserted_count += 1
            logger.info(
                "Item criado: {} (item_id={}, cooperativa={})",
                config_item.reference,
                item_id,
                config_item.cooperativa,
            )

        logger.success(
            "Dispatcher concluído. {} inserido(s), {} pulado(s)",
            inserted_count,
            skipped_count,
        )

        return task.complete(
            variables={
                "project_id": project_id,
                "job_id": job_id,
                "inserted_count": inserted_count,
                "skipped_count": skipped_count,
                "item_ids": item_ids,
            }
        )

    except Exception as exc:
        logger.exception("Falha no Dispatcher")
        return task.failure(
            error_message=str(exc),
            error_details=traceback.format_exc(),
        )
