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
from lib_sisbr_desktop.src.lib_sisbr_desktop.gui.mapeamento import PLATAFORMA_DE_ATENDIMENTO, PLATAFORMA_DE_CREDITO
from lib_sisbr_desktop.src.lib_sisbr_desktop.gui.typer import type_with_retry, write_with_retry
from lib_sisbr_desktop.src.lib_sisbr_desktop.gui.helpers import find_edit_by_rect, get_position_img

from lib_sisbr_desktop.src.lib_sisbr_desktop.gui.helpers import get_position_img


# Caminho dos templates
current_file = Path(__file__).resolve()
# parent.parent = .../lib_sisbr_desktop
lib_project_root = current_file.parent.parent.parent.parent  # Ajuste o número de "parent"
ocr_credito = (lib_project_root / "src" / "lib_sisbr_desktop" / "ocr" / "plataforma_de_credito").resolve()

@retry(times=3, delay_s=2)
def acessa_submodulo(win_modulo, submodulo: str, plataforma: str = "ATENDIMENTO"):
    logger.info("Navegando para o submódulo " + submodulo + " ...")
    # Definir os bounds de acordo com a plataforma
    if plataforma == "PLATAFORMA DE CRÉDITO":
        logger.info("Executando lógica específica para Plataforma de Crédito...")
        # Fazer hover na imagem menu_plataforma_de_credito
        try:
            btn_menu_credito = ocr_credito / "menu_plataforma_de_credito.png"
            menu_position = get_position_img(btn_menu_credito)
            
            if menu_position:
                logger.info(f"Fazendo hover na imagem menu_plataforma_de_credito na posição: {menu_position}")
                for _ in range(5):
                    pyautogui.press('esc')
                    time.sleep(0.5)
                pyautogui.moveTo(menu_position[0], menu_position[1])
                time.sleep(1)
                
                bounds = PLATAFORMA_DE_CREDITO["edit_search_submodulo"]["bounds"]
                logger.info(f"Procurando e clicando no retângulo com bounds: {bounds} (tolerância aumentada)")
                # Aqui, vamos clicar diretamente nas coordenadas do centro do bounds e digitar o texto usando write_with_retry
                x = (bounds[0] + bounds[2]) // 2
                y = (bounds[1] + bounds[3]) // 2
                write_with_retry(x, y, submodulo)               
                time.sleep(3)
                send_keys('{DOWN}{ENTER}')
            else:
                logger.error("Imagem menu_plataforma_de_credito não encontrada")
                raise RuntimeError("Template menu_plataforma_de_credito não encontrado")
        except Exception as e:
            logger.error(f"Erro ao executar lógica da Plataforma de Crédito: {e}")
            raise RuntimeError(f"Erro ao executar lógica da Plataforma de Crédito: {e}")
    elif plataforma == "PLATAFORMA DE ATENDIMENTO":
        try:
            bounds = PLATAFORMA_DE_ATENDIMENTO["edit_search_submodulo"]["bounds"]
            campo_busca_submodulo = find_edit_by_rect(win_modulo, bounds)
        
            # Comportamento comum para ambas as plataformas
            type_with_retry(campo_busca_submodulo, submodulo, wait=2.5)
            time.sleep(3)
            send_keys('{DOWN}{ENTER}')

        except Exception as e:
            logger.error(f"Erro ao executar lógica da Plataforma de Atendimento: {e}")
            raise RuntimeError(f"Erro ao executar lógica da Plataforma de Atendimento: {e}")