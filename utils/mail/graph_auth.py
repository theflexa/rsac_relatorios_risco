"""
Autenticacao Microsoft Graph API via client credentials flow.

Modulo reutilizavel — nao depende de nenhum codigo do projeto.
Unico requisito: ``requests``.

Exemplo de uso::

    token = get_access_token(
        tenant_id="...",
        client_id="...",
        client_secret="...",
    )
"""
from __future__ import annotations

import time

import requests


class GraphAuthError(RuntimeError):
    """Falha ao obter access token do Azure AD."""


def get_access_token(
    *,
    tenant_id: str,
    client_id: str,
    client_secret: str,
    max_retries: int = 3,
    retry_delay: float = 3.0,
) -> str:
    """Obtem access token via OAuth2 client credentials flow.

    Retorna o token como string.  Levanta ``GraphAuthError`` se todas
    as tentativas falharem.
    """
    url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "https://graph.microsoft.com/.default",
        "grant_type": "client_credentials",
    }

    last_error: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.post(url, data=payload, timeout=30)
            data = resp.json()
            if "access_token" in data:
                return data["access_token"]
            last_error = GraphAuthError(
                f"Resposta sem access_token (tentativa {attempt}/{max_retries}): {data}"
            )
        except Exception as exc:
            last_error = exc

        if attempt < max_retries:
            time.sleep(retry_delay)

    raise GraphAuthError(
        f"Falha ao obter access token apos {max_retries} tentativas"
    ) from last_error
