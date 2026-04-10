"""
Envio de e-mail via Microsoft Graph API.

Modulo reutilizavel — depende apenas de ``requests`` e de
``utils.mail.graph_auth``.

Exemplo de uso::

    from utils.mail import send_mail

    send_mail(
        from_email="rpa@empresa.com.br",
        to="dest1@empresa.com.br;dest2@empresa.com.br",
        subject="Relatorio concluido",
        body="<h1>OK</h1>",
        tenant_id="...",
        client_id="...",
        client_secret="...",
    )
"""
from __future__ import annotations

import time

import requests

from utils.mail.graph_auth import get_access_token


class MailSendError(RuntimeError):
    """Falha ao enviar e-mail via Microsoft Graph."""


def send_mail(
    *,
    from_email: str,
    to: str,
    subject: str,
    body: str,
    tenant_id: str,
    client_id: str,
    client_secret: str,
    cc: str | None = None,
    content_type: str = "HTML",
    max_retries: int = 3,
    retry_delay: float = 2.0,
) -> None:
    """Envia um e-mail usando a Graph API ``/sendMail``.

    Args:
        from_email: Remetente (precisa de permissao ``Mail.Send`` no app).
        to: Destinatarios separados por ``;``.
        subject: Assunto.
        body: Corpo (HTML ou texto).
        tenant_id, client_id, client_secret: Credenciais Azure AD.
        cc: Destinatarios em copia, separados por ``;``.
        content_type: ``"HTML"`` ou ``"Text"``.
        max_retries: Tentativas em caso de falha.
        retry_delay: Segundos entre tentativas.

    Raises:
        MailSendError: Se todas as tentativas falharem.
    """
    token = get_access_token(
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret,
    )

    payload = _build_payload(
        to=to,
        subject=subject,
        body=body,
        cc=cc,
        content_type=content_type,
    )

    url = f"https://graph.microsoft.com/v1.0/users/{from_email}/sendMail"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    last_error: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            if resp.status_code == 202:
                return
            last_error = MailSendError(
                f"Status {resp.status_code} (tentativa {attempt}/{max_retries}): {resp.text}"
            )
        except Exception as exc:
            last_error = exc

        if attempt < max_retries:
            time.sleep(retry_delay)

    raise MailSendError(
        f"Falha ao enviar e-mail apos {max_retries} tentativas"
    ) from last_error


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_payload(
    *,
    to: str,
    subject: str,
    body: str,
    cc: str | None,
    content_type: str,
) -> dict:
    message: dict = {
        "subject": subject,
        "body": {
            "contentType": content_type,
            "content": body,
        },
        "toRecipients": _parse_recipients(to),
    }
    if cc:
        message["ccRecipients"] = _parse_recipients(cc)
    return {"message": message, "saveToSentItems": True}


def _parse_recipients(raw: str) -> list[dict]:
    """Converte string ``"a@x.com;b@x.com"`` em lista de recipients Graph."""
    return [
        {"emailAddress": {"address": addr.strip()}}
        for addr in raw.split(";")
        if addr.strip()
    ]
