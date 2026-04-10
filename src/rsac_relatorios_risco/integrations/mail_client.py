"""Re-export de utils.mail para compatibilidade."""
from utils.mail.client import (  # noqa: F401
    send_mail,
    MailSendError,
    _build_payload,
    _parse_recipients,
)
