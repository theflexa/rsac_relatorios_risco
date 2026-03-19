# src/lib_sisbr_desktop/core/trocar_cooperativa.py
import time
import pyautogui
import threading
from loguru import logger
from pathlib import Path

from ..gui.helpers import click_and_verify, get_position_img, get_element_name_by_point, get_element_name_by_rect
from ..gui.typer import write_with_retry

# Caminho dos templates
current_file = Path(__file__).resolve()
# parent.parent = .../lib_sisbr_desktop
lib_project_root = current_file.parent.parent  # Ajuste o número de "parent"
ocr_path = (lib_project_root / "ocr" / "principal").resolve()
btn_trocar_cooperativa = ocr_path / "trocar_cooperativa.png"
edit_nova_cooperativa = ocr_path / "nova_cooperativa.png"
trocando_cooperativa = ocr_path / "trocando_cooperativa.png"
btn_sim = ocr_path / "sim2.png"

def trocar_cooperativa(win_principal, cooperativa: str, max_retentativas: int = 3):
    logger.info(f"Tentando trocar para a cooperativa '{cooperativa}' com até {max_retentativas} tentativas.")

    coop_atual = get_element_name_by_rect("Sisbr 2.0", 366, 125, 436, 143, tolerance=4)

    logger.info(f"Cooperativa atual: {coop_atual}.")

    if not coop_atual.startswith(cooperativa):
        for tentativa in range(1, max_retentativas + 1):
            try:
                logger.info(f"Tentativa {tentativa}/{max_retentativas}...")
                try:
                    win_thread = threading.Thread(target=lambda: win_principal.set_focus())
                    win_thread.daemon = True
                    win_thread.start()
                    win_thread.join(1.0)
                    logger.info("Foco transferido para a janela do Sisbr.")
                except Exception:
                    logger.error("Erro ao transferir o foco para a janela do Sisbr.")
                    pass

                click_and_verify(btn_trocar_cooperativa, edit_nova_cooperativa)

                _, pos = get_position_img(edit_nova_cooperativa, offset_x=130)
                x, y = pos
                write_with_retry(x, y, cooperativa)

                # Clique no botão "LOGAR"
                pyautogui.press('tab', presses=2)  # ajuste se necessário
                pyautogui.press('enter') # primeira tela
                

                click_and_verify(btn_sim, trocando_cooperativa)
                time.sleep (6)
                # Espera imagem aparecer (tratando RuntimeError como "não encontrado")
                _appear_deadline = time.time() + 30
                while True:
                    try:
                        found = get_position_img(trocando_cooperativa, timeout=0)
                    except RuntimeError:
                        found = None
                    if found is not None:
                        break
                    if time.time() > _appear_deadline:
                        raise RuntimeError("Imagem 'trocando_cooperativa' não apareceu no tempo limite.")
                    time.sleep(0.2)
                print("Imagem trocando_cooperativa detectada. Monitorando desaparecimento...")
                # Fica em loop enquanto encontra (tratando RuntimeError como "não encontrado")
                _disappear_deadline = time.time() + 30
                while True:
                    try:
                        still_there = get_position_img(trocando_cooperativa, timeout=3)
                    except RuntimeError:
                        still_there = None
                    if still_there is None:
                        break
                    if time.time() > _disappear_deadline:
                        raise RuntimeError("Imagem 'trocando_cooperativa' não desapareceu no tempo limite.")
                    time.sleep(0.2)

                _coop_change_deadline = time.time() + 30
                while not coop_atual.startswith(cooperativa):
                    coop_atual = get_element_name_by_rect("Sisbr 2.0", 366, 125, 436, 143, tolerance=4)
                    if time.time() > _coop_change_deadline:
                        raise RuntimeError("Cooperativa não atualizou no tempo limite.")
                    time.sleep(1)

                logger.success(f"Cooperativa '{cooperativa}' acessada com sucesso!")
                return

            except Exception as e:
                logger.warning(f"Falha na tentativa {tentativa} de acessar a cooperativa '{cooperativa}': {e}")
                if tentativa < max_retentativas:
                    time.sleep(3)
                else:
                    logger.error(f"Falha final ao acessar a cooperativa '{cooperativa}'.")
                    raise RuntimeError(f"Não foi possível acessar a cooperativa '{cooperativa}'.") from e
    else:
        logger.info(f"Já estava na cooperativa correta: '{cooperativa}'")