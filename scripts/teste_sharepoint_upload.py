"""
Teste isolado de upload para o SharePoint.

Uso:
    python scripts/teste_sharepoint_upload.py caminho/do/arquivo.xlsx

Requer no .env:
    SHAREPOINT_TENANT_ID=...
    SHAREPOINT_CLIENT_ID=...
    SHAREPOINT_CLIENT_SECRET=...
    SHAREPOINT_SITE_URL=https://tenant.sharepoint.com/sites/meusite
    SHAREPOINT_BIBLIOTECA=Documentos Compartilhados
    SHAREPOINT_FOLDER_PATH=Pasta/Subpasta
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv()

from utils.sharepoint import upload_file


def main() -> int:
    if len(sys.argv) < 2:
        print("Uso: python scripts/teste_sharepoint_upload.py <arquivo> [folder_path]")
        print("Se folder_path for omitido, usa SHAREPOINT_FOLDER_PATH do .env")
        return 1

    file_path = Path(sys.argv[1])
    if not file_path.exists():
        print(f"Arquivo nao encontrado: {file_path}")
        return 1

    site_url = os.getenv("SHAREPOINT_SITE_URL", "")
    biblioteca = os.getenv("SHAREPOINT_BIBLIOTECA", "Documentos Compartilhados")
    folder_path = sys.argv[2] if len(sys.argv) > 2 else os.getenv("SHAREPOINT_FOLDER_PATH", "")

    tenant_id = os.getenv("SHAREPOINT_TENANT_ID", "")
    client_id = os.getenv("SHAREPOINT_CLIENT_ID", "")
    client_secret = os.getenv("SHAREPOINT_CLIENT_SECRET", "")

    if not site_url:
        print("Defina SHAREPOINT_SITE_URL no .env")
        return 1

    if not all([tenant_id, client_id, client_secret]):
        print("Credenciais incompletas no .env (SHAREPOINT_TENANT_ID, CLIENT_ID, CLIENT_SECRET)")
        return 1

    print(f"Arquivo:     {file_path}")
    print(f"Site:        {site_url}")
    print(f"Biblioteca:  {biblioteca}")
    print(f"Folder:      {folder_path}")
    print(f"Client ID:   {client_id[:8]}...")
    print()

    web_url = upload_file(
        file_path,
        site_url=site_url,
        folder_path=folder_path,
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret,
        biblioteca=biblioteca,
    )

    print(f"Upload concluido: {web_url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
