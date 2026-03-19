import sys
import os
import argparse
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv(dotenv_path="../.env")

from database import get_items
from collections import defaultdict
from pprint import pprint

if __name__ == "__main__":
    project_id = 53
    items = get_items({"project_id": project_id})
    print(f"Encontrados {len(items)} itens no projeto {project_id}.\n")

    for item in items:
        if (item["status"]) == "pendente":
            print("=============================================================")
            print(item["item_id"])
            print(item["data"].get("nome"))
            print(item["data"].get("loginsisbr"))
            print(item["status"])
            print("=============================================================")
