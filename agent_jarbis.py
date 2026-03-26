"""
Worker Jarbis para o projeto RSAC Relatórios de Risco.

Escuta dois tópicos:
  - Dispatcher: lê Config.xlsx e cria itens no banco (1 por cooperativa)
  - Performer:  processa cada item (Sisbr → RSA → exportar → salvar)

Uso:
  python agent_jarbis.py
"""
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_PATH = PROJECT_ROOT / "src"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from jarbis_external_client.api.authorization import BasicAuth
from jarbis_external_client.api.endpoints import ExternalTaskClient
from jarbis_external_client.model.topic import Topic
from jarbis_external_client.worker import ExternalTaskWorker
from loguru import logger

from config.settings import JARBIS_URL, JARBIS_USER, JARBIS_PASSWORD
from tasks.task_dispatcher import task_dispatcher
from tasks.task_performer import task_performer


def main():
    logger.info("Inicializando Worker RSAC Relatórios de Risco...")

    auth = BasicAuth(
        username=JARBIS_USER,
        password=JARBIS_PASSWORD,
    )

    api_client = ExternalTaskClient(
        base_url=JARBIS_URL,
        auth=auth,
    )

    worker = ExternalTaskWorker(
        worker_id="1",
        fetch_timeout=5000,
        external_task_client=api_client,
    )

    topic_dispatcher = Topic(
        name="Dispatcher",
        lock_duration=120000,       # 2 min (ler Config.xlsx e criar itens)
        retries=3,
        retry_timeout=5000,
    )

    topic_performer = Topic(
        name="Performer",
        lock_duration=900000,       # 15 min (Sisbr + RSA + download)
        retries=3,
        retry_timeout=10000,
    )

    logger.info("Inscrevendo worker nos tópicos Dispatcher e Performer...")
    worker.subscribe(topic_dispatcher, task_dispatcher)
    worker.subscribe(topic_performer, task_performer)

    logger.success("Worker iniciado. Aguardando tarefas do Jarbis...")
    worker.fetch_tasks()


if __name__ == "__main__":
    main()
