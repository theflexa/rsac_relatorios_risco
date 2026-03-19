# C:\Automations\lib_sisbr_desktop\tests\plataforma_atendimento_acesso_cpfcnpj.py
import time
import os
import shutil
import psutil
import pyautogui
import cv2
import numpy as np
from datetime import datetime, timedelta

from loguru import logger
from pywinauto.keyboard import send_keys
from pywinauto.timings import TimeoutError
from pathlib import Path
from lib_sisbr_desktop.src.lib_sisbr_desktop.utils.retry import retry
from lib_sisbr_desktop.src.lib_sisbr_desktop.gui.typer import write_with_retry
from lib_sisbr_desktop.src.lib_sisbr_desktop.gui.helpers import get_position_img, find_first_template_match


current_file = Path(__file__).resolve()
# parent.parent = .../lib_sisbr_desktop
lib_project_root = current_file.parent.parent  # Ajuste o número de "parent"
ocr_path = (lib_project_root / "ocr" / "plataforma_de_atendimento").resolve()

@retry(times=3, delay_s=2)
def acessar_cliente_por_cpf_cnpj(win_modulo, cpf_cnpj: str):
    try:
        win_modulo.set_focus()
        logger.info(f"CPF/CNPJ: {cpf_cnpj}")
        
        templates = [
            ocr_path / "cpfcnpj.png",
            ocr_path / "cliente_pesquisado.png",
        ]
        result = find_first_template_match(templates, threshold=0.90, timeout=20)

        if result:
            template_found, pos = result
            logger.info(f"Match encontrado na imagem: {template_found} {pos}")

            if str(template_found).endswith("cpfcnpj.png"):
                # Digita CPF/CNPJ
                x, y = pos
                write_with_retry(x, y, cpf_cnpj)
                
            elif str(template_found).endswith("cliente_pesquisado.png"):
                # Busca e clica no botão de ação (ou outro campo)
                botao_acao_img = ocr_path / "search.png"
                _, pos = get_position_img(botao_acao_img, threshold=0.87, timeout=5)
                if pos:
                    logger.info(f"Botão de ação encontrado em: {pos}")
                    pyautogui.click(pos)
                    _, pos = get_position_img(ocr_path / "cpfcnpj.png", threshold=0.90, timeout=7)
                    x, y = pos
                    write_with_retry(x, y, cpf_cnpj)                
                else:
                    logger.warning("Botão de ação não encontrado após cliente pesquisado.")
                    raise

            else:
                logger.warning(f"Template inesperado encontrado: {template_found}")

        else:
            logger.warning("Nenhuma imagem de campo ou cliente encontrada. Abortando rotina.")
            raise RuntimeError("Template não encontrado, tentando novamente...")
        
        logger.info("Pressionando ENTER para buscar o cliente...")
        send_keys('{ENTER}')
        time.sleep(3)
        logger.success(f"Cliente com documento '{cpf_cnpj}' buscado. Tela pronta para a próxima etapa.")

    except Exception as e:
        logger.error(f"Erro ao buscar cpf/cnpj: {e}")
        raise
