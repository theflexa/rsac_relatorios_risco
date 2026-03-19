import sys
import os
import time
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import pyautogui
from PIL import Image, ImageChops, ImageStat
from src.lib_sisbr_desktop.gui.mapeamento import RETANGULOS_CONTACORRENTE_RECT, REGIAO_PRINT
from src.lib_sisbr_desktop.utils.screen_utils import area_muda_de_cor, salvar_print_regiao

import re
from src.lib_sisbr_desktop.gui.helpers import verificar_campo_muda_de_cor, double_click_coords

print("Verificando se o campo muda de cor ao clicar no centro do retângulo...")
for idx, coord in enumerate(RETANGULOS_CONTACORRENTE_RECT):
    # Calcula as coordenadas do centro do retângulo definido por 'coord'
    x = (coord['l'] + coord['r']) // 2
    y = (coord['t'] + coord['b']) // 2
    if verificar_campo_muda_de_cor(coord):
        print(f"Retângulo {idx+1} centro (x={x}, y={y}) é CLICÁVEL (mudou de cor ao clicar). Realizando duplo clique...")
        double_click_coords(x, y)
        time.sleep(0.5)
        PASTA_RELATORIOS = Path(project_root) / 'temp' / 'relatorios_finais'
        salvar_print_regiao(*REGIAO_PRINT, PASTA_RELATORIOS)
    else:
        print(f"Retângulo {idx+1} centro (x={x}, y={y}) NÃO mudou de cor ao clicar. Fim da lista de contas.")
        break
    time.sleep(0.3)