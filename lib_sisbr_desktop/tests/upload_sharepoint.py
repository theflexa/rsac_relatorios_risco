import os
import requests
from pathlib import Path
from urllib.parse import quote
from dotenv import load_dotenv
from loguru import logger
import time
import base64
import time as _time

try:
    from msal import ConfidentialClientApplication
except ImportError:
    ConfidentialClientApplication = None
    logger.warning("MSAL não está instalado. Para autenticação via Graph, instale com: pip install msal")

# Carrega variáveis do .env igual aos outros scripts
dotenv_path = os.getenv('UPLOAD_SHAREPOINT_ENV_PATH') or os.path.join(os.path.dirname(__file__), '../.env')
load_dotenv(os.path.abspath(dotenv_path))

TENANT_ID = os.getenv("SHAREPOINT_TENANT_ID")
CLIENT_ID = os.getenv("SHAREPOINT_CLIENT_ID")
CLIENT_SECRET = os.getenv("SHAREPOINT_CLIENT_SECRET")
SITE_URL = os.getenv("SHAREPOINT_SITE_URL")
BIBLIOTECA = os.getenv("SHAREPOINT_BIBLIOTECA")

class SharePointUploadError(Exception):
    """Exceção customizada para erros de upload no SharePoint."""
    pass

def get_access_token_graph(tenant_id=None, client_id=None, client_secret=None, max_retries=3, retry_delay=3):
    """
    Obtém o access token usando MSAL (Microsoft Graph, ConfidentialClientApplication).
    Loga tentativas, sucesso e falha.
    """
    if ConfidentialClientApplication is None:
        logger.error("MSAL não está instalado. Instale com: pip install msal")
        raise ImportError("MSAL não está instalado. Instale com: pip install msal")
    tenant_id = tenant_id or TENANT_ID
    client_id = client_id or CLIENT_ID
    client_secret = client_secret or CLIENT_SECRET
    authority = f"https://login.microsoftonline.com/{tenant_id}"
    scope = ["https://graph.microsoft.com/.default"]
    for tentativa in range(1, max_retries+1):
        logger.info(f"Tentando obter access token (Graph) tentativa {tentativa}/{max_retries}...")
        try:
            app = ConfidentialClientApplication(
                client_id=client_id,
                client_credential=client_secret,
                authority=authority
            )
            token_response = app.acquire_token_for_client(scopes=scope)
            if "access_token" in token_response:
                logger.success("Access token (Graph) obtido com sucesso.")
                return token_response["access_token"]
            else:
                logger.error(f"Erro ao obter token (Graph): {token_response}")
                raise SharePointUploadError(f"Erro ao obter token (Graph): {token_response}")
        except Exception as e:
            logger.error(f"Erro ao obter access token (Graph) (tentativa {tentativa}/{max_retries}): {e}")
            if tentativa == max_retries:
                logger.critical("Falha ao obter access token do Azure AD via Graph.")
                raise SharePointUploadError("Falha ao obter access token do Azure AD via Graph.") from e
            logger.info(f"Aguardando {retry_delay}s para nova tentativa...")
            time.sleep(retry_delay)


def get_site_id_and_drive_id(site_url, biblioteca, access_token):
    """
    Obtém o site_id e drive_id do SharePoint via Microsoft Graph.
    """
    # Extrai o host e o caminho do site
    from urllib.parse import urlparse
    parsed = urlparse(site_url)
    host = parsed.netloc
    path = parsed.path.replace('/sites/', '')
    # Busca o site_id
    url_site = f"https://graph.microsoft.com/v1.0/sites/{host}:/sites/{path}"
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.get(url_site, headers=headers)
    if resp.status_code != 200:
        logger.error(f"Erro ao obter site_id: {resp.status_code} - {resp.text}")
        raise SharePointUploadError(f"Erro ao obter site_id: {resp.status_code} - {resp.text}")
    site_id = resp.json()['id']
    # Busca o drive_id da biblioteca
    url_drives = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives"
    resp = requests.get(url_drives, headers=headers)
    if resp.status_code != 200:
        logger.error(f"Erro ao obter drives: {resp.status_code} - {resp.text}")
        raise SharePointUploadError(f"Erro ao obter drives: {resp.status_code} - {resp.text}")
    # Tenta encontrar o drive pelo nome
    for drive in resp.json().get('value', []):
        if drive['name'].lower() in biblioteca.lower():
            return site_id, drive['id']
    # Se não encontrar, retorna o primeiro (padrão)
    logger.warning(f"Drive com nome '{biblioteca}' não encontrado, usando o primeiro disponível.")
    return site_id, resp.json()['value'][0]['id']


def criar_pasta_graph(site_id, drive_id, pasta_destino, access_token):
    """
    Cria uma pasta (e subpastas) no SharePoint via Graph, se não existir.
    Retorna o webUrl da última pasta criada/checada.
    """
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    partes = pasta_destino.strip('/').split('/')
    caminho = ''
    web_url = None
    for parte in partes:
        caminho = f"{caminho}/{parte}" if caminho else parte
        url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/root:/{caminho}"  # verifica se existe
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            web_url = resp.json().get('webUrl')
            continue  # já existe
        # Cria a pasta
        url_create = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/root:/{caminho}:/children"
        data = {"name": parte, "folder": {}, "@microsoft.graph.conflictBehavior": "replace"}
        resp = requests.post(url_create, headers=headers, json=data)
        if resp.status_code not in (200, 201):
            logger.error(f"Erro ao criar pasta '{caminho}': {resp.status_code} - {resp.text}")
            raise SharePointUploadError(f"Erro ao criar pasta '{caminho}': {resp.status_code} - {resp.text}")
        logger.success(f"Pasta '{caminho}' criada com sucesso.")
        web_url = resp.json().get('webUrl')
    return web_url


def upload_arquivo_graph(site_id, drive_id, pasta_destino, arquivo_path, access_token):
    """
    Faz upload de um arquivo para uma pasta específica no SharePoint via Graph.
    """
    headers = {"Authorization": f"Bearer {access_token}"}
    arquivo = Path(arquivo_path)
    if not arquivo.exists():
        logger.error(f"Arquivo não encontrado: {arquivo_path}")
        raise SharePointUploadError(f"Arquivo não encontrado: {arquivo_path}")
    upload_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/root:/{pasta_destino}/{arquivo.name}:/content"
    with open(arquivo, "rb") as f:
        resp = requests.put(upload_url, headers=headers, data=f)
    if resp.status_code in (200, 201):
        logger.success(f"Arquivo enviado via Graph: {arquivo.name} para pasta {pasta_destino}")
    else:
        logger.error(f"Erro ao enviar via Graph: {resp.status_code} - {resp.text}")
        raise SharePointUploadError(f"Erro ao enviar via Graph: {resp.status_code} - {resp.text}")


def upload_lote_para_pasta_sharepoint(lista_arquivos, nome_pasta, site_url=None, biblioteca=None, tenant_id=None, client_id=None, client_secret=None):
    """
    Faz upload de uma lista de arquivos para uma pasta única no SharePoint via Microsoft Graph.
    Se a pasta não existir, cria. Se existir, faz upload normalmente.
    Todos os erros são tratados e logados. Se algum upload falhar, o processo continua para os demais arquivos.
    Retorna o link webUrl da pasta criada/utilizada.
    """
    logger.info(f"Iniciando upload em lote para pasta '{nome_pasta}' no SharePoint (Graph)...")
    site_url = site_url or SITE_URL
    biblioteca = biblioteca or BIBLIOTECA
    try:
        access_token = get_access_token_graph(tenant_id, client_id, client_secret)
        site_id, drive_id = get_site_id_and_drive_id(site_url, biblioteca, access_token)
        pasta_web_url = criar_pasta_graph(site_id, drive_id, nome_pasta, access_token)
    except Exception as e:
        logger.critical(f"Falha crítica ao preparar upload (Graph): {e}")
        raise
    erros = []
    for arquivo_path in lista_arquivos:
        try:
            upload_arquivo_graph(site_id, drive_id, nome_pasta, arquivo_path, access_token)
        except Exception as e:
            logger.error(f"Falha ao enviar {arquivo_path}: {e}")
            erros.append((arquivo_path, str(e)))
    if erros:
        logger.warning(f"{len(erros)} arquivos falharam no upload. Veja detalhes acima.")
    else:
        logger.info(f"Upload em lote para pasta '{nome_pasta}' finalizado com sucesso (Graph).")
    if pasta_web_url:
        logger.info(f"Acesse a pasta no SharePoint: {pasta_web_url}")
    return pasta_web_url


def get_item_id_from_share_link(share_link, access_token):
    """
    Obtém drive_id, item_id e web_url de uma pasta a partir de um link compartilhado do SharePoint.
    Loga detalhes do processo e erros.
    """
    logger.info(f"Buscando item_id a partir do link compartilhado: {share_link}")
    share_id = base64.urlsafe_b64encode(share_link.encode("utf-8")).decode("utf-8").rstrip("=")
    url = f"https://graph.microsoft.com/v1.0/shares/u!{share_id}/driveItem"
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.get(url, headers=headers)
    logger.info(f"GET {url} -> {resp.status_code}")
    if resp.status_code != 200:
        logger.error(f"Erro ao obter item_id pelo link: {resp.status_code} - {resp.text}")
        raise SharePointUploadError(f"Erro ao obter item_id pelo link: {resp.status_code} - {resp.text}")
    item = resp.json()
    drive_id = item['parentReference']['driveId']
    item_id = item['id']
    web_url = item['webUrl']
    logger.success(f"Obtido drive_id: {drive_id}, item_id: {item_id}, web_url: {web_url}")
    return drive_id, item_id, web_url


def upload_arquivo_para_itemid(drive_id, item_id, arquivo_path, access_token):
    """
    Faz upload de um arquivo para uma pasta específica do SharePoint via item_id (Graph).
    Loga início, sucesso, falha e detalhes do upload.
    """
    arquivo = Path(arquivo_path)
    if not arquivo.exists():
        logger.error(f"Arquivo não encontrado: {arquivo_path}")
        raise SharePointUploadError(f"Arquivo não encontrado: {arquivo_path}")
    upload_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{item_id}:/{arquivo.name}:/content"
    headers = {"Authorization": f"Bearer {access_token}"}
    logger.info(f"Iniciando upload do arquivo '{arquivo.name}' para item_id {item_id} (drive {drive_id})")
    with open(arquivo, "rb") as f:
        resp = requests.put(upload_url, headers=headers, data=f)
    logger.info(f"PUT {upload_url} -> {resp.status_code}")
    if resp.status_code in (200, 201):
        logger.success(f"Arquivo enviado via Graph: {arquivo.name} para item_id {item_id}")
    else:
        logger.error(f"Erro ao enviar via Graph: {resp.status_code} - {resp.text}")
        raise SharePointUploadError(f"Erro ao enviar via Graph: {resp.status_code} - {resp.text}")


def verificar_ou_criar_subpasta_em_itemid(drive_id, parent_item_id, nome_subpasta, access_token):
    """
    Verifica se uma subpasta existe dentro de um item_id (pasta). Se não existir, cria.
    Loga todas as etapas, urls, status e resultados.
    """
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    logger.info(f"Verificando existência da subpasta '{nome_subpasta}' em item_id {parent_item_id} (drive {drive_id})")
    url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{parent_item_id}/children?$filter=name eq '{nome_subpasta}' and folder ne null"
    resp = requests.get(url, headers=headers)
    logger.info(f"GET {url} -> {resp.status_code}")
    if resp.status_code == 200 and resp.json().get('value'):
        subpasta = resp.json()['value'][0]
        logger.info(f"Subpasta '{nome_subpasta}' já existe. item_id: {subpasta['id']} url: {subpasta.get('webUrl')}")
        return subpasta['id'], subpasta.get('webUrl')
    # Cria a subpasta
    url_create = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{parent_item_id}/children"
    data = {"name": nome_subpasta, "folder": {}, "@microsoft.graph.conflictBehavior": "replace"}
    logger.info(f"Criando subpasta '{nome_subpasta}' em {url_create} ...")
    resp = requests.post(url_create, headers=headers, json=data)
    logger.info(f"POST {url_create} -> {resp.status_code}")
    if resp.status_code in (200, 201):
        subpasta = resp.json()
        logger.success(f"Subpasta '{nome_subpasta}' criada com sucesso. item_id: {subpasta['id']} url: {subpasta.get('webUrl')}")
        return subpasta['id'], subpasta.get('webUrl')
    else:
        logger.error(f"Erro ao criar subpasta '{nome_subpasta}': {resp.status_code} - {resp.text}")
        raise SharePointUploadError(f"Erro ao criar subpasta '{nome_subpasta}': {resp.status_code} - {resp.text}")


def arquivos_existentes_na_pasta(drive_id, pasta_item_id, access_token):
    """
    Retorna uma lista dos nomes dos arquivos existentes na pasta (item_id) do SharePoint.
    Loga a busca, resposta bruta e o resultado.
    """
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{pasta_item_id}/children?$select=name"
    logger.info(f"Buscando arquivos existentes na pasta item_id {pasta_item_id} (drive {drive_id})")
    resp = requests.get(url, headers=headers)
    logger.info(f"GET {url} -> {resp.status_code}")
    logger.debug(f"Resposta bruta da API de arquivos existentes: {resp.text}")
    if resp.status_code != 200:
        logger.error(f"Erro ao buscar arquivos existentes na pasta: {resp.status_code} - {resp.text}")
        raise SharePointUploadError(f"Erro ao buscar arquivos existentes na pasta: {resp.status_code} - {resp.text}")
    arquivos = [item['name'] for item in resp.json().get('value', []) if 'file' in item]
    if arquivos:
        logger.info(f"Arquivos já existentes na pasta: {arquivos}")
    else:
        logger.info("Nenhum arquivo existente encontrado na pasta.")
    return arquivos


def upload_lote_para_link_sharepoint(lista_arquivos, share_link, nome_subpasta, tenant_id=None, client_id=None, client_secret=None):
    """
    Faz upload de uma lista de arquivos para uma subpasta (por CPF) dentro de uma pasta do SharePoint a partir de um link compartilhado.
    Cria/verifica a subpasta e faz upload para ela. Retorna o web_url da subpasta.
    Sempre faz o upload (PUT), sobrescrevendo arquivos se já existirem.
    Loga todas as etapas, parâmetros e erros. Tenta cada upload até 5 vezes em caso de erro, com sleep de 1s entre tentativas.
    """
    import time as _time
    logger.info("="*60)
    logger.info(f"INICIANDO UPLOAD EM LOTE PARA SHAREPOINT VIA LINK COMPARTILHADO")
    logger.info(f"Arquivos a enviar: {[str(Path(p).name) for p in lista_arquivos]}")
    logger.info(f"Link compartilhado: {share_link}")
    logger.info(f"Subpasta (CPF): {nome_subpasta}")
    logger.info(f"Tenant: {tenant_id or TENANT_ID} | Client ID: {client_id or CLIENT_ID}")
    t0 = _time.time()
    try:
        access_token = get_access_token_graph(tenant_id, client_id, client_secret)
        logger.info(f"Token obtido: {access_token[:10]}...{access_token[-10:]}")
        _time.sleep(1)
        logger.info(f"Resolvendo link compartilhado...")
        drive_id, parent_item_id, parent_web_url = get_item_id_from_share_link(share_link, access_token)
        logger.info(f"Pasta base: drive_id={drive_id}, item_id={parent_item_id}, web_url={parent_web_url}")
        subpasta_id, subpasta_web_url = verificar_ou_criar_subpasta_em_itemid(drive_id, parent_item_id, nome_subpasta, access_token)
        logger.info(f"Subpasta destino: item_id={subpasta_id}, web_url={subpasta_web_url}")
        _time.sleep(1)
    except Exception as e:
        logger.critical(f"Falha crítica ao preparar upload via link: {e}")
        raise
    erros = []
    enviados = []
    for arquivo_path in lista_arquivos:
        nome_arquivo = Path(arquivo_path).name
        try:
            tam = Path(arquivo_path).stat().st_size
        except Exception:
            tam = 'desconhecido'
        logger.info(f"Iniciando upload do arquivo: {nome_arquivo} | Tamanho: {tam} bytes | Caminho local: {arquivo_path}")
        t1 = _time.time()
        for tentativa in range(1, 6):
            try:
                logger.info(f"Tentativa {tentativa}/5 para upload do arquivo '{nome_arquivo}'...")
                upload_arquivo_para_itemid(drive_id, subpasta_id, arquivo_path, access_token)
                t2 = _time.time()
                logger.success(f"Upload concluído: {nome_arquivo} | Tempo: {t2-t1:.2f}s (tentativa {tentativa})")
                enviados.append(nome_arquivo)
                break
            except Exception as e:
                logger.error(f"Erro ao enviar '{nome_arquivo}' (tentativa {tentativa}/5): {e}")
                if tentativa == 5:
                    logger.critical(f"Falha definitiva ao enviar '{nome_arquivo}' após 5 tentativas.")
                    erros.append((arquivo_path, str(e)))
                else:
                    logger.info("Aguardando 1s para nova tentativa...")
                    _time.sleep(1)
        _time.sleep(1)
    tF = _time.time()
    logger.info("-"*60)
    if enviados:
        logger.success(f"Arquivos enviados com sucesso: {enviados}")
    if erros:
        logger.warning(f"{len(erros)} arquivos falharam no upload. Veja detalhes acima.")
    logger.info(f"Tempo total do processo: {tF-t0:.2f}s")
    if subpasta_web_url:
        logger.info(f"Acesse a subpasta no SharePoint: {subpasta_web_url}")
    logger.info("="*60)
    return subpasta_web_url 