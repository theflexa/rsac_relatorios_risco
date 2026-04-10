"""
Upload de arquivos para SharePoint via Microsoft Graph API.

Modulo reutilizavel — depende apenas de ``requests`` e de
``utils.microsoft_graph``.

Exemplo de uso::

    from utils.sharepoint import upload_file

    web_url = upload_file(
        Path("relatorio.xlsx"),
        site_url="https://tenant.sharepoint.com/sites/meusite",
        folder_path="Pasta/Subpasta",
        tenant_id="...",
        client_id="...",
        client_secret="...",
        biblioteca="Documentos Compartilhados",
    )
"""
from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

import requests

from utils.mail.graph_auth import get_access_token


class SharePointUploadError(RuntimeError):
    """Erro durante upload para o SharePoint."""


# ---------------------------------------------------------------------------
# API publica
# ---------------------------------------------------------------------------

def upload_file(
    file_path: str | Path,
    *,
    site_url: str,
    folder_path: str,
    tenant_id: str,
    client_id: str,
    client_secret: str,
    biblioteca: str = "Documentos Compartilhados",
) -> str:
    """Faz upload de um arquivo para uma pasta do SharePoint.

    Cria as pastas intermediarias automaticamente caso nao existam.

    Args:
        file_path: Caminho local do arquivo.
        site_url: URL do site SharePoint (ex: ``https://tenant.sharepoint.com/sites/meusite``).
        folder_path: Caminho da pasta dentro da biblioteca (ex: ``Pasta/Sub``).
        tenant_id, client_id, client_secret: Credenciais Azure AD.
        biblioteca: Nome da biblioteca de documentos.
            Default: ``"Documentos Compartilhados"``.

    Returns:
        Web URL do arquivo enviado.

    Raises:
        SharePointUploadError: Em caso de falha na operacao.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise SharePointUploadError(f"Arquivo nao encontrado: {file_path}")

    token = get_access_token(
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret,
    )

    site_host, site_path = _parse_site_url(site_url)
    site_id = _get_site_id(site_host, site_path, token)
    drive_id = _get_drive_by_name(site_id, biblioteca, token)
    _ensure_folder(site_id, drive_id, folder_path, token)
    return _upload(site_id, drive_id, folder_path, file_path, token)


def build_rsac_folder_path(
    base_folder: str,
    *,
    competencia: str,
    cooperativa: str,
) -> str:
    """Monta folder path com subdiretorios dinamicos RSAC.

    Formato: ``{base_folder}/{yyyy} - Ações RSAC/{MM-yyyy}/{cooperativa}``

    Args:
        base_folder: Folder path base dentro da biblioteca
            (ex: ``DESENVOLVIMENTO/DESENVOLVEDORES/.../Saida``).
        competencia: No formato ``MM/AAAA`` (ex: ``03/2026``).
        cooperativa: Codigo da cooperativa (ex: ``3042``).
    """
    mes, ano = competencia.split("/")
    suffix = f"{ano} - Ações RSAC/{mes}-{ano}/{cooperativa}"
    return f"{base_folder.rstrip('/')}/{suffix}"


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _parse_site_url(url: str) -> tuple[str, str]:
    """Extrai host e site path de uma URL do SharePoint.

    Exemplo:
        URL: https://tenant.sharepoint.com/sites/meusite
        Retorna: ("tenant.sharepoint.com", "sites/meusite")
    """
    parsed = urlparse(url)
    host = parsed.netloc
    parts = [p for p in parsed.path.split("/") if p]

    if len(parts) < 2 or parts[0] != "sites":
        raise SharePointUploadError(
            f"URL do site SharePoint invalida (esperado https://host/sites/nome): {url}"
        )

    return host, f"sites/{parts[1]}"


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _get_site_id(host: str, site_path: str, token: str) -> str:
    url = f"https://graph.microsoft.com/v1.0/sites/{host}:/{site_path}"
    resp = requests.get(url, headers=_headers(token), timeout=30)
    if resp.status_code != 200:
        raise SharePointUploadError(
            f"Erro ao obter site_id ({resp.status_code}): {resp.text}"
        )
    return resp.json()["id"]


def _get_drive_by_name(site_id: str, biblioteca: str, token: str) -> str:
    """Busca drive pelo nome da biblioteca (ex: 'Documentos Compartilhados')."""
    url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives"
    resp = requests.get(url, headers=_headers(token), timeout=30)
    if resp.status_code != 200:
        raise SharePointUploadError(
            f"Erro ao listar drives ({resp.status_code}): {resp.text}"
        )
    biblioteca_lower = biblioteca.lower()
    for drive in resp.json().get("value", []):
        if drive.get("name", "").lower() == biblioteca_lower:
            return drive["id"]
    raise SharePointUploadError(
        f"Biblioteca '{biblioteca}' nao encontrada no site. "
        f"Disponiveis: {[d.get('name') for d in resp.json().get('value', [])]}"
    )


def _ensure_folder(site_id: str, drive_id: str, folder_path: str, token: str) -> None:
    if not folder_path:
        return

    hdrs = {**_headers(token), "Content-Type": "application/json"}
    parts = folder_path.strip("/").split("/")
    current = ""

    for part in parts:
        current = f"{current}/{part}" if current else part
        check_url = (
            f"https://graph.microsoft.com/v1.0/sites/{site_id}"
            f"/drives/{drive_id}/root:/{current}"
        )
        resp = requests.get(check_url, headers=_headers(token), timeout=30)
        if resp.status_code == 200:
            continue

        parent = "/".join(current.split("/")[:-1])
        if parent:
            create_url = (
                f"https://graph.microsoft.com/v1.0/sites/{site_id}"
                f"/drives/{drive_id}/root:/{parent}:/children"
            )
        else:
            create_url = (
                f"https://graph.microsoft.com/v1.0/sites/{site_id}"
                f"/drives/{drive_id}/root/children"
            )

        body = {
            "name": part,
            "folder": {},
            "@microsoft.graph.conflictBehavior": "replace",
        }
        resp = requests.post(create_url, headers=hdrs, json=body, timeout=30)
        if resp.status_code not in (200, 201):
            raise SharePointUploadError(
                f"Erro ao criar pasta '{current}' ({resp.status_code}): {resp.text}"
            )


def _upload(
    site_id: str,
    drive_id: str,
    folder_path: str,
    file_path: Path,
    token: str,
) -> str:
    upload_url = (
        f"https://graph.microsoft.com/v1.0/sites/{site_id}"
        f"/drives/{drive_id}/root:/{folder_path}/{file_path.name}:/content"
    )
    with open(file_path, "rb") as f:
        resp = requests.put(
            upload_url,
            headers=_headers(token),
            data=f,
            timeout=120,
        )

    if resp.status_code not in (200, 201):
        raise SharePointUploadError(
            f"Erro ao enviar '{file_path.name}' ({resp.status_code}): {resp.text}"
        )
    return resp.json().get("webUrl", "")
