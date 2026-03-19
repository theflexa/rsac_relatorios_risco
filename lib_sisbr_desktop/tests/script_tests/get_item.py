import sys
import os
import argparse
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv(dotenv_path="../.env")
from database import get_item_by_id


ITEM_ID = 150875


def main() -> None:
    item = get_item_by_id(ITEM_ID)
    print(item)

if __name__ == "__main__":
    main()