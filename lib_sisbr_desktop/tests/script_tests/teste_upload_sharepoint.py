import sys
import time
from pathlib import Path
from loguru import logger

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import os
import ssl
import urllib3
import requests
from pathlib import Path

# Desabilitar warnings SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configurações do SharePoint (substitua pelos seus valores)
TENANT_ID = "071ab648-205b-4c78-9447-ad15f4b3a8d2"  # Seu tenant ID
CLIENT_ID = "seu_client_id_aqui"  # Seu client ID
CLIENT_SECRET = "seu_client_secret_aqui"  # Seu client secret
SHARE_LINK = "https://sicoobbr.sharepoint.com/sites/..."  # Seu link compartilhado

def get_access_token_graph(tenant_id, client_id, client_secret, max_retries=3, retry_delay=3):
    """
    Obtém o access token usando MSAL com SSL desabilitado.
    """
    try:
        from msal import ConfidentialClientApplication
    except ImportError:
        logger.error("MSAL não está instalado. Instale com: pip install msal")
        raise ImportError("MSAL não está instalado. Instale com: pip install msal")
    
    authority = f"https://login.microsoftonline.com/{tenant_id}"
    scope = ["https://graph.microsoft.com/.default"]
    
    for tentativa in range(1, max_retries+1):
        logger.info(f"Tentativa {tentativa}/{max_retries} de obter access token...")
        try:
            app = ConfidentialClientApplication(
                client_id=client_id,
                client_credential=client_secret,
                authority=authority
            )
            
            token_response = app.acquire_token_for_client(scopes=scope)
            if "access_token" in token_response:
                logger.success("Access token obtido com sucesso!")
                return token_response["access_token"]
            else:
                logger.error(f"Erro ao obter token: {token_response}")
                raise Exception(f"Erro ao obter token: {token_response}")
        except Exception as e:
            logger.error(f"Erro na tentativa {tentativa}: {e}")
            if tentativa == max_retries:
                raise
            time.sleep(retry_delay)

def get_item_id_from_share_link(share_link, access_token):
    """
    Obtém drive_id, item_id e web_url de uma pasta a partir de um link compartilhado.
    """
    import base64
    
    # Configurar sessão HTTP com SSL desabilitado
    session = requests.Session()
    session.verify = False
    session.trust_env = False
    
    logger.info(f"Buscando item_id a partir do link: {share_link}")
    share_id = base64.urlsafe_b64encode(share_link.encode("utf-8")).decode("utf-8").rstrip("=")
    url = f"https://graph.microsoft.com/v1.0/shares/u!{share_id}/driveItem"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    resp = session.get(url, headers=headers)
    logger.info(f"GET {url} -> {resp.status_code}")
    
    if resp.status_code != 200:
        logger.error(f"Erro ao obter item_id: {resp.status_code} - {resp.text}")
        raise Exception(f"Erro ao obter item_id: {resp.status_code} - {resp.text}")
    
    item = resp.json()
    drive_id = item['parentReference']['driveId']
    item_id = item['id']
    web_url = item['webUrl']
    
    logger.success(f"Obtido drive_id: {drive_id}, item_id: {item_id}")
    return drive_id, item_id, web_url

def upload_arquivo_para_itemid(drive_id, item_id, arquivo_path, access_token):
    """
    Faz upload de um arquivo para uma pasta específica do SharePoint.
    """
    # Configurar sessão HTTP com SSL desabilitado
    session = requests.Session()
    session.verify = False
    session.trust_env = False
    
    arquivo = Path(arquivo_path)
    if not arquivo.exists():
        logger.error(f"Arquivo não encontrado: {arquivo_path}")
        raise Exception(f"Arquivo não encontrado: {arquivo_path}")
    
    upload_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{item_id}:/{arquivo.name}:/content"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    logger.info(f"Fazendo upload do arquivo '{arquivo.name}'...")
    
    with open(arquivo, "rb") as f:
        resp = session.put(upload_url, headers=headers, data=f)
    
    logger.info(f"PUT {upload_url} -> {resp.status_code}")
    
    if resp.status_code in (200, 201):
        logger.success(f"Arquivo '{arquivo.name}' enviado com sucesso!")
        return resp.json()
    else:
        logger.error(f"Erro no upload: {resp.status_code} - {resp.text}")
        raise Exception(f"Erro no upload: {resp.status_code} - {resp.text}")

def criar_subpasta(drive_id, parent_item_id, nome_subpasta, access_token):
    """
    Cria uma subpasta dentro de uma pasta existente.
    """
    # Configurar sessão HTTP com SSL desabilitado
    session = requests.Session()
    session.verify = False
    session.trust_env = False
    
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    
    # Verificar se a subpasta já existe
    url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{parent_item_id}/children?$filter=name eq '{nome_subpasta}' and folder ne null"
    resp = session.get(url, headers=headers)
    
    if resp.status_code == 200 and resp.json().get('value'):
        subpasta = resp.json()['value'][0]
        logger.info(f"Subpasta '{nome_subpasta}' já existe. item_id: {subpasta['id']}")
        return subpasta['id']
    
    # Criar a subpasta
    url_create = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{parent_item_id}/children"
    data = {"name": nome_subpasta, "folder": {}, "@microsoft.graph.conflictBehavior": "replace"}
    
    logger.info(f"Criando subpasta '{nome_subpasta}'...")
    resp = session.post(url_create, headers=headers, json=data)
    
    if resp.status_code in (200, 201):
        subpasta = resp.json()
        logger.success(f"Subpasta '{nome_subpasta}' criada com sucesso. item_id: {subpasta['id']}")
        return subpasta['id']
    else:
        logger.error(f"Erro ao criar subpasta: {resp.status_code} - {resp.text}")
        raise Exception(f"Erro ao criar subpasta: {resp.status_code} - {resp.text}")

def testar_upload_sharepoint():
    """
    Função principal para testar o upload de arquivos para o SharePoint.
    """
    logger.info("Iniciando teste de upload para o SharePoint...")
    
    try:
        # 1. Obter access token
        logger.info("1. Obtendo access token...")
        access_token = get_access_token_graph(TENANT_ID, CLIENT_ID, CLIENT_SECRET)
        
        # 2. Obter informações do link compartilhado
        logger.info("2. Obtendo informações do link compartilhado...")
        drive_id, item_id, web_url = get_item_id_from_share_link(SHARE_LINK, access_token)
        
        # 3. Criar subpasta de teste
        logger.info("3. Criando subpasta de teste...")
        nome_subpasta = f"teste_upload_{int(time.time())}"
        subpasta_item_id = criar_subpasta(drive_id, item_id, nome_subpasta, access_token)
        
        # 4. Criar arquivo de teste
        logger.info("4. Criando arquivo de teste...")
        arquivo_teste = project_root / "temp" / "arquivo_teste.txt"
        arquivo_teste.parent.mkdir(parents=True, exist_ok=True)
        
        with open(arquivo_teste, "w", encoding="utf-8") as f:
            f.write(f"Este é um arquivo de teste criado em {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("Teste de upload para o SharePoint com SSL desabilitado.\n")
        
        # 5. Fazer upload do arquivo
        logger.info("5. Fazendo upload do arquivo...")
        resultado = upload_arquivo_para_itemid(drive_id, subpasta_item_id, arquivo_teste, access_token)
        
        # 6. Limpar arquivo de teste
        logger.info("6. Limpando arquivo de teste...")
        arquivo_teste.unlink()
        
        logger.success("Teste de upload concluído com sucesso!")
        logger.info(f"Arquivo enviado para: {resultado.get('webUrl', 'N/A')}")
        
        return True
        
    except Exception as e:
        logger.error(f"Erro durante o teste: {e}")
        return False

if __name__ == "__main__":
    # Configurar logging
    logger.remove()
    logger.add(sys.stderr, level="INFO", format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>")
    
    # Verificar se as configurações estão definidas
    if CLIENT_ID == "seu_client_id_aqui" or CLIENT_SECRET == "seu_client_secret_aqui":
        logger.error("Por favor, configure CLIENT_ID e CLIENT_SECRET no arquivo antes de executar o teste.")
        sys.exit(1)
    
    if SHARE_LINK == "https://sicoobbr.sharepoint.com/sites/...":
        logger.error("Por favor, configure SHARE_LINK no arquivo antes de executar o teste.")
        sys.exit(1)
    
    # Executar teste
    sucesso = testar_upload_sharepoint()
    
    if sucesso:
        logger.success("Teste executado com sucesso!")
    else:
        logger.error("Teste falhou!")
        sys.exit(1) 