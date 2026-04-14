"""Configuração do projeto RSAC — lê variáveis de ambiente (.env)."""
from __future__ import annotations

import os
from typing import Dict


_ENV_MAP = {
    "projectName": "PROJECT_NAME",
    "projectDescription": "PROJECT_DESCRIPTION",
    "projectStatus": "PROJECT_STATUS",
    "projectOwner": "PROJECT_OWNER",
    "projectDev": "PROJECT_DEV",
    "projectStartDate": "PROJECT_START_DATE",
    "ExScreenshotsName": "EX_SCREENSHOTS_NAME",
}

_DEFAULTS = {
    "projectName": "RSAC Relatórios de Risco",
    "projectDescription": "Exportação automatizada de relatórios de Riscos Social, Ambiental e Climático",
    "projectStatus": "Desenvolvimento",
    "projectOwner": "Inteligência Estratégica",
    "projectDev": "Guilherme Flexa",
    "projectStartDate": "2026-03-16",
    "ExScreenshotsName": "RSACExportacaoRelatorioRisco_",
}


def load_project_config(config_path=None) -> Dict[str, str]:
    """Carrega config do projeto a partir de variáveis de ambiente (.env)."""
    config = dict(_DEFAULTS)
    for key, env_var in _ENV_MAP.items():
        value = os.getenv(env_var, "")
        if value:
            config[key] = value
    return config


_DEFAULT_REPORT_PATTERN = "relatorio_{cooperativa}_{competencia}.xlsx"


def build_report_filename(cooperativa: str, competencia: str) -> str:
    """Monta nome do arquivo de relatório usando o padrão do .env."""
    pattern = os.getenv("REPORT_FILENAME_PATTERN", _DEFAULT_REPORT_PATTERN)
    competencia_clean = competencia.replace("/", "")
    return pattern.format(cooperativa=cooperativa, competencia=competencia_clean)
