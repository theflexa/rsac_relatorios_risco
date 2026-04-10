"""Servico de e-mail do RSAC — monta e envia resumo de execucao."""
from __future__ import annotations

import os

from utils.mail import send_mail, build_status_email


def build_summary_subject(status: str, competencia: str) -> str:
    return f"RSAC {competencia} - {status}"


def build_summary_body(
    *,
    competencia: str,
    concluidos: list[str],
    pendentes: list[str],
    erros: list[str],
) -> str:
    concluidos_texto = ", ".join(concluidos) if concluidos else "nenhum"
    pendentes_texto = ", ".join(pendentes) if pendentes else "nenhum"
    erros_texto = " | ".join(erros) if erros else "nenhum"
    return (
        f"Competência: {competencia}\n"
        f"Concluídos: {concluidos_texto}\n"
        f"Pendentes: {pendentes_texto}\n"
        f"Erros: {erros_texto}"
    )


def build_summary_html(
    *,
    concluidos: list[str],
    erros: list[str],
    competencia: str = "",
    project_name: str = "",
) -> str:
    """Monta HTML completo do resumo usando template reutilizavel Sicoob."""
    items = [(ref, True) for ref in concluidos] + [(ref, False) for ref in erros]
    return build_status_email(
        project_name=project_name or os.getenv("PROJECT_NAME", ""),
        intro="Segue abaixo o resultado da execu\u00e7\u00e3o referente a baixa dos relat\u00f3rios de risco no Sisbr 3.0.",
        items=items,
        competencia=competencia,
        col_label="Cooperativa",
    )


def send_result_email(
    summary: dict,
    *,
    item_destinatarios: str,
    settings: dict[str, str],
    competencia: str,
    mail_from: str,
    tenant_id: str,
    client_id: str,
    client_secret: str,
) -> None:
    """Envia e-mail de RESULTADO por item. TO = item.Destinatarios, CC = Settings.MailDestinatarioCC."""
    concluidos = summary.get("concluidos", [])
    erros = summary.get("erros_sistemicos", [])

    status = "Concluido" if not erros else "Concluido com erros"
    subject = settings.get("MailSubject", build_summary_subject(status, competencia))

    body = build_summary_html(
        concluidos=concluidos,
        erros=erros,
        competencia=competencia,
    )

    cc = settings.get("MailDestinatarioCC", "")

    if not item_destinatarios:
        return

    send_mail(
        from_email=mail_from,
        to=item_destinatarios,
        subject=f"{subject} - {competencia} - {status}",
        body=body,
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret,
        cc=cc or None,
    )


def send_exception_email(
    *,
    error_message: str,
    reference: str,
    settings: dict[str, str],
    competencia: str,
    mail_from: str,
    tenant_id: str,
    client_id: str,
    client_secret: str,
) -> None:
    """Envia e-mail de EXCECAO. TO = Settings.MailDestinatarioResultado, CC = Settings.MailDestinatarioCC."""
    to = settings.get("MailDestinatarioResultado", "")
    cc = settings.get("MailDestinatarioCC", "")

    if not to:
        return

    subject = settings.get("MailSubject", "RSAC")

    body = build_status_email(
        project_name=os.getenv("PROJECT_NAME", ""),
        intro=f"Uma falha foi identificada no processamento do item <strong>{reference}</strong>.",
        items=[(reference, False)],
        competencia=competencia,
        col_label="Item",
        extra_html_bottom=f'<p style="color:#D32F2F;font-size:13px;"><strong>Erro:</strong> {error_message}</p>',
    )

    send_mail(
        from_email=mail_from,
        to=to,
        subject=f"{subject} - {competencia} - ERRO - {reference}",
        body=body,
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret,
        cc=cc or None,
    )


# Alias retrocompativel
def send_summary(
    summary: dict,
    *,
    settings: dict[str, str],
    competencia: str,
    mail_from: str,
    tenant_id: str,
    client_id: str,
    client_secret: str,
) -> None:
    """Alias que envia resultado para MailDestinatarioResultado (fallback)."""
    to = settings.get("MailDestinatarioResultado", "")
    send_result_email(
        summary,
        item_destinatarios=to,
        settings=settings,
        competencia=competencia,
        mail_from=mail_from,
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret,
    )
