import pyautogui
import time
from pathlib import Path
from PIL import Image, ImageChops, ImageStat

# Desabilita o fail-safe do PyAutoGUI para evitar interrupções
pyautogui.FAILSAFE = False

def area_muda_de_cor(img1, img2, threshold=10):
    diff = ImageChops.difference(img1, img2)
    stat = ImageStat.Stat(diff)
    return sum(stat.mean) > threshold

def screenshot_regiao(left, top, right, bottom, save_path=None):
    width = right - left
    height = bottom - top
    screenshot = pyautogui.screenshot(region=(left, top, width, height))
    if save_path:
        screenshot.save(str(save_path))
    return screenshot

def salvar_print_regiao(left, top, right, bottom, pasta_destino, nome_prefixo='print_regiao'):
    pasta_destino = Path(pasta_destino)
    pasta_destino.mkdir(parents=True, exist_ok=True)
    nome_arquivo = f'{nome_prefixo}_{int(time.time())}.png'
    caminho_arquivo = pasta_destino / nome_arquivo
    screenshot_regiao(left, top, right, bottom, save_path=caminho_arquivo)
    print(f"Screenshot da região salva em: {caminho_arquivo}")
    return caminho_arquivo 