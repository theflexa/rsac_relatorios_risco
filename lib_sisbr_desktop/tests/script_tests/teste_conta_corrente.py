import sys
import time
from pathlib import Path
from loguru import logger

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import pyautogui
from PIL import Image, ImageChops, ImageStat
import pytesseract
import os
from src.lib_sisbr_desktop.gui.mapeamento import RETANGULOS_CONTACORRENTE_RECT, REGIAO_PRINT
from src.lib_sisbr_desktop.utils.screen_utils import  salvar_print_regiao

from src.lib_sisbr_desktop.gui.helpers import verificar_campo_muda_de_cor, double_click_coords, get_position_img
from src.lib_sisbr_desktop.gui.helpers import get_position_img

from PIL import ImageOps
import re
from PIL import Image, ImageEnhance
import pytesseract

# Caminho dos templates
current_file = Path(__file__).resolve()
# parent.parent = .../lib_sisbr_desktop
lib_project_root = current_file.parent.parent  # Ajuste o número de "parent"
ocr_path = (lib_project_root / "src" / "lib_sisbr_desktop" / "ocr" / "plataforma_de_atendimento").resolve()


def baixar_relatorio_conta_corrente(win_modulo, id_item: str, pasta_destino_final: str):
    """
    Executa o fluxo completo de download do relatório de Conta Corrente.
    """
    logger.info("Iniciando processo de download do relatório Conta Corrente.")
    win_modulo.set_focus()

    logger.info("Verificando se o campo muda de cor ao clicar no centro do retângulo...")
    caminhos_prints = []
    for idx, coord in enumerate(RETANGULOS_CONTACORRENTE_RECT):
        # Calcula as coordenadas do centro do retângulo definido por 'coord'
        x = (coord['l'] + coord['r']) // 2
        y = (coord['t'] + coord['b']) // 2
        if verificar_campo_muda_de_cor(coord):
            logger.info(f"Retângulo {idx+1} centro (x={x}, y={y}) é CLICÁVEL (mudou de cor ao clicar). Realizando duplo clique...")
            double_click_coords(x, y)
            time.sleep(0.5)

            # Salva o print
            caminho_print = salvar_print_regiao(*REGIAO_PRINT, pasta_destino_final)
            # Após tirar o print, clicar no botão voltar
            caminho_img_voltar = ocr_path / 'conta_corrente' / 'voltar.png'
            timeout_voltar = 10  # segundos
            t0 = time.time()
            while True:
                pos_voltar = get_position_img(str(caminho_img_voltar), threshold=0.8, timeout=2)
                if pos_voltar:
                    _, (xv, yv) = pos_voltar
                    logger.info(f"Clicando no botão voltar em ({xv}, {yv})")
                    pyautogui.click(xv, yv)
                    time.sleep(0.5)
                    break
                elif time.time() - t0 > timeout_voltar:
                    logger.error("Timeout ao aguardar o botão voltar aparecer na tela!")
                    raise RuntimeError("Timeout ao aguardar o botão voltar aparecer na tela!")
                else:
                    logger.info("Botão voltar ainda não apareceu, aguardando...")
                    time.sleep(0.5)

            caminhos_prints.append(str(caminho_print))

        else:
            logger.warning(f"Retângulo {idx+1} centro (x={x}, y={y}) NÃO mudou de cor ao clicar. Fim da lista de contas.")
            break
        time.sleep(0.3)
    # Renomeia todos os prints de Conta Corrente no final, igual ao faturamento/renda
    caminhos_baixados_dict = {}
    for idx, caminho in enumerate(caminhos_prints):
        nome_final = f"ContaCorrente_{idx}_{id_item}.png"
        novo_caminho = os.path.join(os.path.dirname(caminho), nome_final)
        os.rename(caminho, novo_caminho)
        logger.info(f"Print renomeado para: {novo_caminho}")
        caminhos_baixados_dict[(idx, 0)] = novo_caminho
    logger.success("Relatórios Conta Corrente salvos com sucesso.")
    return caminhos_baixados_dict

class DummyWin:
    def set_focus(self):
        pass

if __name__ == "__main__":
    win_modulo = DummyWin()
    id_item = "123"
    PASTA_RELATORIOS_FINAL = str(project_root / "temp/relatorios_finais")
    logger.info("Iniciando teste de download do relatório Conta Corrente...")
    caminhos_prints = baixar_relatorio_conta_corrente(win_modulo, id_item, PASTA_RELATORIOS_FINAL)
    logger.info(f"Caminhos dos prints salvos: {caminhos_prints}")
