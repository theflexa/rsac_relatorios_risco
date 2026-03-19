import os
import requests
from datetime import datetime, timezone
import argparse
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../.env'))

def ensure_project(config):
    DATABASE_URL = os.getenv("DATABASE_URL")
    DATABASE_API_KEY = os.getenv("DATABASE_API_KEY")
    url = DATABASE_URL.rstrip("/") + "/projects"
    headers = {
        "apikey": DATABASE_API_KEY,
        "Authorization": f"Bearer {DATABASE_API_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=representation"
    }
    params = {"project_name": f"eq.{config['projectName']}"}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    results = response.json()
    if results:
        return results[0]["project_id"]
    payload = {
        "project_name": config["projectName"],
        "description": config["projectDescription"],
        "status": config["projectStatus"],
        "created_by": config["projectDev"],
        "owner": config["projectOwner"]
    }
    if config.get("projectStartDate"):
        payload["start_date"] = config["projectStartDate"]
    post_resp = requests.post(url, headers=headers, json=payload)
    post_resp.raise_for_status()
    created = post_resp.json()
    return created[0]["project_id"]

def insert_job(config):
    DATABASE_URL = os.getenv("DATABASE_URL")
    DATABASE_API_KEY = os.getenv("DATABASE_API_KEY")
    url = DATABASE_URL.rstrip("/") + "/jobs"
    headers = {
        "apikey": DATABASE_API_KEY,
        "Authorization": f"Bearer {DATABASE_API_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=representation"
    }
    execution_date = datetime.now(timezone.utc).isoformat()
    payload = {
        "project_id": int(config["project_id"]),
        "execution_date": execution_date,
        "status": "aguardando"  # Enum permitido: aguardando, em andamento, cancelado, finalizado
    }
    print("URL:", url)
    print("HEADERS:", headers)
    print("PAYLOAD:", payload)
    resp = requests.post(url, headers=headers, json=payload)
    print("RESP STATUS:", resp.status_code)
    print("RESP TEXT:", resp.text)
    resp.raise_for_status()
    created = resp.json()
    return created[0]["job_id"]

def ensure_job(config):
    # Como a criação é sempre permitida, só faz o insert
    return insert_job(config)

def insert_items_with_project_and_job(config, items, current_queue_item=None):
    config = config.copy()  # Para não modificar original
    config["project_id"] = ensure_project(config)
    config["job_id"] = ensure_job(config)
    return insert_items(config, items, current_queue_item)

def insert_items(config, items, current_queue_item=None):
    DATABASE_URL = os.getenv("DATABASE_URL")
    DATABASE_API_KEY = os.getenv("DATABASE_API_KEY")
    url = DATABASE_URL.rstrip("/") + "/items"
    headers = {
        "apikey": DATABASE_API_KEY,
        "Authorization": f"Bearer {DATABASE_API_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=representation"
    }
    
    payloads = []
    for item in items:
        payload = {
            "project_id": config["project_id"],
            "job_id": config["job_id"],
            "data": item["jsonData"],  # CAMPO OBRIGATÓRIO NA TABELA (jsonb)
            "status": item.get("status", "pendente"),  # Enum: sucesso, pendente, exceção negocial, erro sistêmico, processando, cancelado
            "reference": item.get("Reference")
        }
        if current_queue_item and "item_id" in current_queue_item:
            payload["parent_id"] = current_queue_item["item_id"]
        payloads.append(payload)
    resp = requests.post(url, headers=headers, json=payloads)
    resp.raise_for_status()
    return resp.json()

def get_items(config):
    DATABASE_URL = os.getenv("DATABASE_URL")
    DATABASE_API_KEY = os.getenv("DATABASE_API_KEY")
    url = DATABASE_URL.rstrip("/") + "/items"
    headers = {
        "apikey": DATABASE_API_KEY,
        "Authorization": f"Bearer {DATABASE_API_KEY}"
    }
    params = {
        "project_id": f"eq.{config['project_id']}"
    }
    if "job_id" in config:
        params["job_id"] = f"eq.{config['job_id']}"
    resp = requests.get(url, headers=headers, params=params)
    resp.raise_for_status()
    return resp.json()

def get_item_by_id(item_id):
    DATABASE_URL = os.getenv("DATABASE_URL")
    DATABASE_API_KEY = os.getenv("DATABASE_API_KEY")
    url = DATABASE_URL.rstrip("/") + "/items"
    headers = {
        "apikey": DATABASE_API_KEY,
        "Authorization": f"Bearer {DATABASE_API_KEY}"
    }
    params = {
        "item_id": f"eq.{item_id}"
    }
    resp = requests.get(url, headers=headers, params=params)
    resp.raise_for_status()
    result = resp.json()
    return result[0] if result else None

def update_item(item_id, status=None, json_data=None):
    DATABASE_URL = os.getenv("DATABASE_URL")
    DATABASE_API_KEY = os.getenv("DATABASE_API_KEY")
    url = DATABASE_URL.rstrip("/") + f"/items?item_id=eq.{item_id}"
    headers = {
        "apikey": DATABASE_API_KEY,
        "Authorization": f"Bearer {DATABASE_API_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    payload = {}
    if status:
        payload["status"] = status
    if json_data:
        payload["data"] = json_data
    resp = requests.patch(url, headers=headers, json=payload)
    resp.raise_for_status()
    return resp.json()

def collect_process():
    parser = argparse.ArgumentParser()
    parser.add_argument("--item-id", type=int, required=True)
    args = parser.parse_args()
    item_id = args.item_id

    result = get_item_by_id(item_id)

    if not result or not isinstance(result, dict):
        print(f"❌ Nenhum item válido encontrado com id={item_id}")
        exit(1)

    # --- Extrair os dados internos do item ---
    processo = result.get("data", {})
    nome_processo = processo.get("nome_processo", "").strip()

    # --- Classificação do processo ---
    cadastros = []
    bloqueios = []
    desbloqueios = []

    if nome_processo == "Bloqueio":
        bloqueios.append(processo)
    elif nome_processo == "desbloqueio":
        desbloqueios.append(processo)
    elif nome_processo == "Gestão de Identidade":
        cadastros.append(processo)
    else:
        print(f"⚠ Processo com nome_processo desconhecido: {nome_processo}")

    # --- Resultado de retorno ---
    print(f"✅ Item ID {item_id} classificado como: {nome_processo}")
    print(f"Cadastros: {len(cadastros)} | Bloqueios: {len(bloqueios)} | Desbloqueios: {len(desbloqueios)}")
    return cadastros, bloqueios, desbloqueios
