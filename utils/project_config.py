"""Configuração estática do projeto RSAC no Jarbis."""
from __future__ import annotations

from typing import Dict


def load_project_config() -> Dict[str, str]:
    return {
        "projectName": "RSAC Relatórios de Risco",
        "projectDescription": "Exportação automatizada de relatórios de Riscos Social, Ambiental e Climático",
        "projectStatus": "Desenvolvimento",
        "projectOwner": "Inteligência Estratégica",
        "projectDev": "Guilherme Flexa",
        "projectStartDate": "2026-03-16",
    }
