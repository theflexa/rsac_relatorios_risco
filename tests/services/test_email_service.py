from rsac_relatorios_risco.integrations.mail_client import build_mail_message
from rsac_relatorios_risco.services.email_service import (
    build_summary_body,
    build_summary_subject,
)


def test_build_summary_subject_and_body_include_concluded_pending_and_errors():
    subject = build_summary_subject(status="parcial", competencia="03/2026")
    body = build_summary_body(
        competencia="03/2026",
        concluidos=["3333", "4444"],
        pendentes=["5555"],
        erros=["Falha ao subir SharePoint da 4444"],
    )

    assert subject == "RSAC 03/2026 - parcial"
    assert "Competência: 03/2026" in body
    assert "Concluídos: 3333, 4444" in body
    assert "Pendentes: 5555" in body
    assert "Erros: Falha ao subir SharePoint da 4444" in body


def test_build_mail_message_returns_transport_payload():
    message = build_mail_message(
        to="time@sicoob.com",
        subject="RSAC 03/2026 - parcial",
        body="Resumo",
    )

    assert message == {
        "to": "time@sicoob.com",
        "subject": "RSAC 03/2026 - parcial",
        "body": "Resumo",
    }
