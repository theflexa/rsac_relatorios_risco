"""
Teste isolado de envio de e-mail via Microsoft Graph.

Uso:
    python scripts/teste_email.py destinatario@empresa.com.br

Requer no .env:
    EMAIL_TENANT_ID=... (ou SHAREPOINT_TENANT_ID como fallback)
    EMAIL_CLIENT_ID=... (ou SHAREPOINT_CLIENT_ID como fallback)
    EMAIL_CLIENT_SECRET=... (ou SHAREPOINT_CLIENT_SECRET como fallback)
    MAIL_FROM=... (ou FROM_EMAIL como fallback)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv()

from utils.mail import send_mail


def _email_credentials() -> dict[str, str]:
    return {
        "tenant_id": os.getenv("EMAIL_TENANT_ID") or os.getenv("SHAREPOINT_TENANT_ID", ""),
        "client_id": os.getenv("EMAIL_CLIENT_ID") or os.getenv("SHAREPOINT_CLIENT_ID", ""),
        "client_secret": os.getenv("EMAIL_CLIENT_SECRET") or os.getenv("SHAREPOINT_CLIENT_SECRET", ""),
    }


def main() -> int:
    if len(sys.argv) < 2:
        print("Uso: python scripts/teste_email.py <destinatario> [assunto]")
        return 1

    to = sys.argv[1]
    subject = sys.argv[2] if len(sys.argv) > 2 else "Teste de e-mail RPA"

    mail_from = os.getenv("MAIL_FROM") or os.getenv("FROM_EMAIL", "")
    creds = _email_credentials()

    if not mail_from:
        print("Defina MAIL_FROM ou FROM_EMAIL no .env")
        return 1

    if not all(creds.values()):
        print("Credenciais incompletas no .env (EMAIL_TENANT_ID/CLIENT_ID/CLIENT_SECRET ou SHAREPOINT_*)")
        return 1

    print(f"De:        {mail_from}")
    print(f"Para:      {to}")
    print(f"Assunto:   {subject}")
    print(f"Client ID: {creds['client_id'][:8]}...")
    print()

    body = (
        "<h3>Teste de e-mail RPA</h3>"
        "<p>Este e-mail foi enviado automaticamente pelo script de teste.</p>"
        "<p>Se voce recebeu, o envio via Microsoft Graph esta funcionando.</p>"
    )

    send_mail(
        from_email=mail_from,
        to=to,
        subject=subject,
        body=body,
        **creds,
    )

    print("E-mail enviado com sucesso!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
