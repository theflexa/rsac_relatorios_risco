"""
Camada de acesso ao banco via PostgREST (estilo Supabase).

Funções reutilizáveis para orquestração Jarbis: projects, jobs, items.

Configuração esperada (.env):
- DATABASE_URL e DATABASE_API_KEY
- Alternância DEV/PROD (opcional):
  - DATABASE_PROFILE=DEV ou PROD
  - DATABASE_URL_DEV/DATABASE_API_KEY_DEV e/ou DATABASE_URL_PROD/DATABASE_API_KEY_PROD
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests
from loguru import logger


ProjectConfig = Dict[str, Any]
JsonValue = Any


# === Configuração do banco (DEV/PROD) ===

def _db_profile() -> str:
    return os.getenv("DATABASE_PROFILE", "").strip().upper()


def _db_env(base_name: str) -> Optional[str]:
    profile = _db_profile()
    if profile:
        value = os.getenv(f"{base_name}_{profile}")
        if value:
            return value
    return os.getenv(base_name)


def _require_db_env(base_name: str) -> str:
    value = _db_env(base_name)
    if value:
        return value
    profile = _db_profile()
    if profile:
        raise RuntimeError(
            f"Variável de ambiente obrigatória não definida: {base_name} (ou {base_name}_{profile})"
        )
    raise RuntimeError(f"Variável de ambiente obrigatória não definida: {base_name}")


def has_database_config() -> bool:
    return bool((_db_env("DATABASE_URL") or "").strip()) and bool((_db_env("DATABASE_API_KEY") or "").strip())


def _base_url() -> str:
    return _require_db_env("DATABASE_URL").rstrip("/")


def _headers(*, prefer: Optional[str] = None) -> Dict[str, str]:
    api_key = _require_db_env("DATABASE_API_KEY")
    headers: Dict[str, str] = {
        "apikey": api_key,
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if prefer:
        headers["Prefer"] = prefer
    return headers


def _utc_now_z() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# === Projects ===

def ensure_project(config: ProjectConfig) -> int:
    url = f"{_base_url()}/projects"
    params = {"project_name": f"eq.{config['projectName']}"}

    response = requests.get(url, headers=_headers(), params=params, timeout=60)
    response.raise_for_status()

    results = response.json() or []
    if results:
        return int(results[0]["project_id"])

    payload: Dict[str, Any] = {
        "project_name": config["projectName"],
        "description": config.get("projectDescription", ""),
        "status": config.get("projectStatus", ""),
        "created_by": config.get("projectDev", ""),
        "owner": config.get("projectOwner", ""),
    }
    project_start_date = str(config.get("projectStartDate", "")).strip()
    if project_start_date:
        payload["start_date"] = project_start_date

    create = requests.post(
        url,
        headers=_headers(prefer="resolution=merge-duplicates,return=representation"),
        json=payload,
        timeout=60,
    )
    create.raise_for_status()

    created = create.json() or []
    if not created:
        raise RuntimeError("Falha ao criar projeto: resposta vazia")
    return int(created[0]["project_id"])


# === Jobs ===

def insert_job(*, project_id: int, status: str = "em andamento") -> int:
    url = f"{_base_url()}/jobs"
    payload = {
        "project_id": int(project_id),
        "execution_date": _utc_now_z(),
        "status": status,
    }
    response = requests.post(
        url,
        headers=_headers(prefer="return=representation"),
        json=payload,
        timeout=60,
    )
    response.raise_for_status()
    created = response.json() or []
    if not created:
        raise RuntimeError("Falha ao criar job: resposta vazia")
    return int(created[0]["job_id"])


def update_job(job_id: int, *, status: str) -> Dict[str, Any]:
    url = f"{_base_url()}/jobs"
    params = {"job_id": f"eq.{int(job_id)}"}
    response = requests.patch(
        url,
        headers=_headers(prefer="return=representation"),
        params=params,
        json={"status": status},
        timeout=60,
    )
    response.raise_for_status()
    results = response.json() or []
    return results[0] if results else {}


# === Items ===

def insert_item(
    *,
    project_id: int,
    job_id: int,
    data: JsonValue,
    status: str = "pendente",
    reference: Optional[str] = None,
    attempts: Optional[List[Dict[str, Any]]] = None,
) -> int:
    url = f"{_base_url()}/items"
    payload: Dict[str, Any] = {
        "project_id": int(project_id),
        "job_id": int(job_id),
        "data": data,
        "status": status,
        "attempts": attempts if attempts is not None else [],
    }
    if reference is not None:
        payload["reference"] = reference

    response = requests.post(
        url,
        headers=_headers(prefer="return=representation"),
        json=[payload],
        timeout=60,
    )
    response.raise_for_status()
    created = response.json() or []
    if not created:
        raise RuntimeError("Falha ao criar item: resposta vazia")
    return int(created[0]["item_id"])


def get_item_by_id(item_id: int) -> Optional[Dict[str, Any]]:
    url = f"{_base_url()}/items"
    params = {"item_id": f"eq.{int(item_id)}"}
    response = requests.get(url, headers=_headers(), params=params, timeout=60)
    response.raise_for_status()
    results = response.json() or []
    return results[0] if results else None


def get_items(
    *,
    project_id: int,
    job_id: Optional[int] = None,
    status: Optional[str] = None,
) -> List[Dict[str, Any]]:
    url = f"{_base_url()}/items"
    params: Dict[str, str] = {"project_id": f"eq.{int(project_id)}"}
    if job_id is not None:
        params["job_id"] = f"eq.{int(job_id)}"
    if status is not None:
        params["status"] = f"eq.{status}"
    response = requests.get(url, headers=_headers(), params=params, timeout=60)
    response.raise_for_status()
    return response.json() or []


def reference_exists(project_id: int, reference: str) -> bool:
    url = f"{_base_url()}/items"
    params = {
        "project_id": f"eq.{int(project_id)}",
        "reference": f"eq.{reference}",
        "limit": "1",
    }
    response = requests.get(url, headers=_headers(), params=params, timeout=60)
    response.raise_for_status()
    return bool(response.json())


def update_item(
    item_id: int,
    *,
    status: Optional[str] = None,
    data: Optional[JsonValue] = None,
    attempts: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    url = f"{_base_url()}/items"
    params = {"item_id": f"eq.{int(item_id)}"}
    payload: Dict[str, Any] = {}
    if status is not None:
        payload["status"] = status
    if data is not None:
        payload["data"] = data
    if attempts is not None:
        payload["attempts"] = attempts

    response = requests.patch(
        url,
        headers=_headers(prefer="return=representation"),
        params=params,
        json=payload,
        timeout=60,
    )
    response.raise_for_status()
    results = response.json() or []
    return results[0] if results else {}


def _merge_json(existing: JsonValue, new: JsonValue) -> JsonValue:
    if existing is None:
        return new
    if isinstance(existing, dict) and isinstance(new, dict):
        merged = dict(existing)
        for key, new_value in new.items():
            if key in merged:
                merged[key] = _merge_json(merged[key], new_value)
            else:
                merged[key] = new_value
        return merged
    return new


def update_item_merge(
    item_id: int,
    *,
    status: Optional[str] = None,
    data: Optional[JsonValue] = None,
) -> Dict[str, Any]:
    current = get_item_by_id(item_id)
    if not current:
        raise RuntimeError(f"Item não encontrado: item_id={item_id}")
    merged_data: Optional[JsonValue] = None
    if data is not None:
        merged_data = _merge_json(current.get("data"), data)
    return update_item(item_id, status=status, data=merged_data)
