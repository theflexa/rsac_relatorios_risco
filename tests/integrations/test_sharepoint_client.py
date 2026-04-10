from utils.sharepoint.client import (
    build_rsac_folder_path,
    _parse_site_url,
)
import pytest


def test_build_rsac_folder_path_formats_correctly():
    result = build_rsac_folder_path(
        "DESENVOLVIMENTO/DESENVOLVEDORES/Saida",
        competencia="03/2026",
        cooperativa="3042",
    )
    assert result == (
        "DESENVOLVIMENTO/DESENVOLVEDORES/Saida"
        "/2026 - Ações RSAC/03-2026/3042"
    )


def test_build_rsac_folder_path_strips_trailing_slash():
    result = build_rsac_folder_path(
        "Pasta/Sub/",
        competencia="12/2025",
        cooperativa="4001",
    )
    assert result == "Pasta/Sub/2025 - Ações RSAC/12-2025/4001"


def test_parse_site_url_extracts_host_and_site():
    host, site_path = _parse_site_url(
        "https://tenant.sharepoint.com/sites/meusite"
    )
    assert host == "tenant.sharepoint.com"
    assert site_path == "sites/meusite"


def test_parse_site_url_ignores_extra_path():
    host, site_path = _parse_site_url(
        "https://tenant.sharepoint.com/sites/meusite/extra/stuff"
    )
    assert host == "tenant.sharepoint.com"
    assert site_path == "sites/meusite"


def test_parse_site_url_rejects_invalid_url():
    with pytest.raises(Exception, match="URL do site SharePoint invalida"):
        _parse_site_url("https://example.com/nope")
