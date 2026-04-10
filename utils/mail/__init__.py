"""
Pacote de e-mail reutilizavel — envio via Microsoft Graph + template Sicoob.

Exemplo de uso::

    from utils.mail import send_mail, build_status_email

    html = build_status_email(
        project_name="Meu Projeto",
        intro="Segue abaixo o resultado do processamento.",
        items=[("item1", True), ("item2", False)],
    )
    send_mail(
        from_email="rpa@empresa.com.br",
        to="dest@empresa.com.br",
        subject="Resultado",
        body=html,
        tenant_id="...",
        client_id="...",
        client_secret="...",
    )
"""
from utils.mail.client import send_mail, MailSendError  # noqa: F401
from utils.mail.graph_auth import get_access_token, GraphAuthError  # noqa: F401
from utils.mail.template import build_status_email  # noqa: F401
