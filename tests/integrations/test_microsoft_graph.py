from unittest.mock import patch, MagicMock

from utils.mail.graph_auth import (
    get_access_token,
    GraphAuthError,
)
import pytest


def _mock_response(json_data, status_code=200):
    resp = MagicMock()
    resp.json.return_value = json_data
    resp.status_code = status_code
    return resp


@patch("utils.mail.graph_auth.requests.post")
def test_get_access_token_returns_token_on_success(mock_post):
    mock_post.return_value = _mock_response({"access_token": "tok123"})

    token = get_access_token(
        tenant_id="t", client_id="c", client_secret="s",
    )

    assert token == "tok123"
    call_kwargs = mock_post.call_args
    assert "oauth2/v2.0/token" in call_kwargs.args[0]
    assert call_kwargs.kwargs["data"]["grant_type"] == "client_credentials"


@patch("utils.mail.graph_auth.requests.post")
def test_get_access_token_raises_after_retries(mock_post):
    mock_post.return_value = _mock_response({"error": "invalid_client"})

    with pytest.raises(GraphAuthError, match="Falha ao obter access token"):
        get_access_token(
            tenant_id="t", client_id="c", client_secret="s",
            max_retries=1, retry_delay=0,
        )
