from dotenv import load_dotenv
import os
from pathlib import Path

# Carrega o .env da raiz do projeto rsac_relatorios_risco
env_path = str(Path(__file__).resolve().parent.parent.parent.parent / ".env")
load_dotenv(dotenv_path=env_path)
print("caminho do .env", env_path)
SISBR_EXE = os.getenv("SISBR_EXE")
USUARIO = os.getenv("USUARIO")
SENHA = os.getenv("SENHA")