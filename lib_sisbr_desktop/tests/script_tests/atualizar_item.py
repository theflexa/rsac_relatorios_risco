import sys
import os
import argparse
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv(dotenv_path="../.env")

from database import update_item
from collections import defaultdict
from pprint import pprint


ITEM_IDS = [
    150875
]


def main() -> None:
    print(f"Atualizando {len(ITEM_IDS)} item(s) para status 'processando'...")
    for item_id in ITEM_IDS:
        try:
            resp = update_item(item_id, status="pendente")
            print(f"{item_id} -> OK: {resp}")
        except Exception as exc:
            print(f"{item_id} -> ERRO: {exc}")


if __name__ == "__main__":
    main()


