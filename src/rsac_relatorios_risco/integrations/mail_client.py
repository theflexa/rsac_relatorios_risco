def build_mail_message(to: str, subject: str, body: str) -> dict:
    return {
        "to": to,
        "subject": subject,
        "body": body,
    }
