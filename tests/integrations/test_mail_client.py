from unittest.mock import patch, MagicMock

from utils.mail.client import (
    send_mail,
    _build_payload,
    _parse_recipients,
    MailSendError,
)
import pytest


def test_parse_recipients_splits_semicolons():
    result = _parse_recipients("a@x.com; b@x.com;c@x.com")
    assert result == [
        {"emailAddress": {"address": "a@x.com"}},
        {"emailAddress": {"address": "b@x.com"}},
        {"emailAddress": {"address": "c@x.com"}},
    ]


def test_parse_recipients_ignores_empty_entries():
    result = _parse_recipients("a@x.com;;")
    assert len(result) == 1


def test_build_payload_includes_cc_when_provided():
    payload = _build_payload(
        to="a@x.com",
        subject="Test",
        body="<p>Hi</p>",
        cc="b@x.com",
        content_type="HTML",
    )
    assert "ccRecipients" in payload["message"]
    assert payload["message"]["body"]["contentType"] == "HTML"
    assert payload["saveToSentItems"] is True


def test_build_payload_omits_cc_when_none():
    payload = _build_payload(
        to="a@x.com", subject="Test", body="Hi",
        cc=None, content_type="Text",
    )
    assert "ccRecipients" not in payload["message"]


@patch("utils.mail.client.get_access_token", return_value="tok")
@patch("utils.mail.client.requests.post")
def test_send_mail_succeeds_on_202(mock_post, mock_token):
    mock_post.return_value = MagicMock(status_code=202)

    send_mail(
        from_email="rpa@x.com",
        to="dest@x.com",
        subject="OK",
        body="body",
        tenant_id="t", client_id="c", client_secret="s",
    )

    assert mock_post.called
    url = mock_post.call_args.args[0]
    assert "rpa@x.com" in url


@patch("utils.mail.client.get_access_token", return_value="tok")
@patch("utils.mail.client.requests.post")
def test_send_mail_raises_after_retries(mock_post, mock_token):
    mock_post.return_value = MagicMock(status_code=400, text="Bad Request")

    with pytest.raises(MailSendError, match="Falha ao enviar"):
        send_mail(
            from_email="rpa@x.com",
            to="dest@x.com",
            subject="Fail",
            body="body",
            tenant_id="t", client_id="c", client_secret="s",
            max_retries=1, retry_delay=0,
        )
