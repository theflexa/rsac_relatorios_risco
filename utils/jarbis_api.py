"""Cliente REST para a API do Jarbis (Camunda)."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import requests
from loguru import logger
from requests.auth import HTTPBasicAuth


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Variável de ambiente obrigatória não definida: {name}")
    return value


def _format_variable(value: Any) -> Dict[str, Any]:
    if value is None:
        return {"value": None, "type": "Null"}
    if isinstance(value, bool):
        return {"value": value, "type": "Boolean"}
    if isinstance(value, int):
        return {"value": value, "type": "Integer"}
    if isinstance(value, (dict, list)):
        return {"value": json.dumps(value, ensure_ascii=False), "type": "Json"}
    return {"value": str(value), "type": "String"}


def format_camunda_variables(values: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {key: _format_variable(value) for key, value in (values or {}).items()}


def start_process_instance(
    process_key: str,
    *,
    variables: Optional[Dict[str, Any]] = None,
    business_key: Optional[str] = None,
) -> Dict[str, Any]:
    base_url = _require_env("JARBIS_BASE_URL").rstrip("/")
    user = _require_env("JARBIS_USERNAME")
    password = _require_env("JARBIS_PASSWORD")

    key = (process_key or "").strip()
    if not key:
        raise ValueError("process_key não pode ser vazio")

    url = f"{base_url}/process-definition/key/{key}/start"
    payload: Dict[str, Any] = {}
    if variables:
        payload["variables"] = format_camunda_variables(variables)
    if business_key:
        payload["businessKey"] = str(business_key)

    response = requests.post(
        url,
        auth=HTTPBasicAuth(user, password),
        json=payload,
        timeout=60,
    )
    response.raise_for_status()

    data = response.json() if response.content else {}
    logger.info(
        "Instância iniciada no Jarbis. process_key={} id={}",
        key,
        data.get("id") or data.get("processInstanceId"),
    )
    return data
