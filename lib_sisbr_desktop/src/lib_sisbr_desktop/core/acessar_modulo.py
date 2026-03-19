# src/lib_sisbr_desktop/core/acessar_modulo.py
import time
from pywinauto.keyboard import send_keys
from pathlib import Path
import pyautogui
import threading
from loguru import logger

from ..gui.helpers import find_edit_by_rect
from ..gui.typer import type_with_retry
from ..gui.mapeamento import CAMPOS_ACESSO_MODULO_RECT 
from ..utils.window import get_window_by_title, get_browser_with_tab
from ..gui.helpers import get_position_img
from ..utils.utils import limpar_restauracao_edge, fechar_todas_instancias_sisbr

def acessar_modulo(win_principal, nome_modulo: str, max_retentativas: int = 3):
    """
    Acessa um módulo do Sisbr, com lógica de retentativa.
    Retorna o objeto da janela do módulo (WindowSpecification) ou lança um erro.
    """
    try:
        # Verificação prévia
        base_ocr = Path(r"C:\Automations\fase_3\lib_sisbr_desktop\src\lib_sisbr_desktop\ocr\navegador")
        try:
            if nome_modulo.upper() == "PAINEL COMERCIAL":
                # Mitiga banner de restauração antes de reutilizar
                
                # Para PAINEL COMERCIAL, procurar por navegador com a aba
                win_existente = get_browser_with_tab("Painel Comercial", timeout=3)
                try:
                    win_thread = threading.Thread(target=lambda: win_existente.set_focus())
                    win_thread.daemon = True
                    win_thread.start()
                    win_thread.join(1.0)
                    logger.info("Foco transferido para a janela do Sisbr.")
                except Exception:
                    logger.error("Erro ao transferir o foco para a janela do Sisbr.")
                    pass
                # Maximizar a janela (sem fullscreen)
                win_existente.maximize()
                # Após abrir/reutilizar, tentar clicar em 'restaurar' se presente
                try:
                    restaurar_img = base_ocr / "restaurar.png"
                    if restaurar_img.exists():
                        result = get_position_img(restaurar_img, threshold=0.5, timeout=3)
                        if result:
                            _, (x, y) = result
                            pyautogui.moveTo(x, y)
                            pyautogui.click()
                            logger.info("Clique em 'restaurar' realizado.")
                            
                except Exception:
                    pass
                logger.success(f"Módulo '{nome_modulo}' já estava aberto no navegador. Reutilizado com sucesso.")
                return win_existente

            if nome_modulo.upper() == "COBRANÇA BANCÁRIA 3.0":
                # Mitiga banner de restauração antes de reutilizar
                
                # Para COBRANÇA BANCÁRIA, procurar por navegador com a aba
                win_existente = get_browser_with_tab("Cobrança Bancária", timeout=3)
                try:
                    win_thread = threading.Thread(target=lambda: win_existente.set_focus())
                    win_thread.daemon = True
                    win_thread.start()
                    win_thread.join(1.0)
                    logger.info("Foco transferido para a janela do Sisbr.")
                except Exception:
                    logger.error("Erro ao transferir o foco para a janela do Sisbr.")
                    pass
                # Maximizar a janela (sem fullscreen)
                win_existente.maximize()
                # Após abrir/reutilizar, tentar clicar em 'restaurar' se presente
                try:
                    restaurar_img = base_ocr / "restaurar.png"
                    if restaurar_img.exists():
                        result = get_position_img(restaurar_img, threshold=0.5, timeout=3)
                        if result:
                            _, (x, y) = result
                            pyautogui.moveTo(x, y)
                            pyautogui.click()
                            logger.info("Clique em 'restaurar' realizado.")
                except Exception:
                    pass
                logger.success(f"Módulo '{nome_modulo}' já estava aberto no navegador. Reutilizado com sucesso.")
                return win_existente
            else:
                # Para outros módulos, usar a verificação padrão
                win_existente = get_window_by_title(
                    titulo=nome_modulo,
                    app=win_principal.app,
                    timeout=3  # curto, só pra checar existência
                )
                try:
                    win_thread = threading.Thread(target=lambda: win_existente.set_focus())
                    win_thread.daemon = True
                    win_thread.start()
                    win_thread.join(1.0)
                    logger.info("Foco transferido para a janela do Sisbr.")
                except Exception:
                    logger.error("Erro ao transferir o foco para a janela do Sisbr.")
                    pass
                logger.success(f"Módulo '{nome_modulo}' já estava aberto. Reutilizado com sucesso.")
                return win_existente
        except Exception:
            logger.info(f"Módulo '{nome_modulo}' não está aberto. Iniciando tentativa de acesso...")
            

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
                
                bounds = CAMPOS_ACESSO_MODULO_RECT["campo_busca_modulo"]["bounds"]
                try:
                    campo_destino = find_edit_by_rect(win_principal, bounds, tolerance=2)
                except RuntimeError as err:
                    if "Nenhum Edit encontrado" in str(err):
                        logger.error("Campo de busca do módulo não localizado. Encerrando SISBR e relançando o erro.")
                        fechar_todas_instancias_sisbr()
                        raise
                    raise
                
                type_with_retry(campo_destino, nome_modulo)
                time.sleep(1)  # Aguardar processamento da digitação
                
                send_keys("{ENTER}")
                time.sleep(1)  # Aguardar processamento do Enter
                pyautogui.moveTo(50, 224)
                pyautogui.click(clicks=2, interval=0.1)
                time.sleep(2)  # Aguardar processamento do duplo clique
                
                if nome_modulo.upper() == "PAINEL COMERCIAL":
                    limpar_restauracao_edge()
                    # Para PAINEL COMERCIAL, aguardar o navegador abrir com a aba
                    win_modulo = get_browser_with_tab("Painel Comercial", timeout=15)
                    # Maximizar a janela (sem fullscreen)
                    win_modulo.maximize()
                    # Tentar clicar em 'restaurar'
                    try:
                        restaurar_img = base_ocr / "restaurar.png"
                        if restaurar_img.exists():
                            result = get_position_img(restaurar_img, threshold=0.8, timeout=3)
                            if result:
                                _, (x, y) = result
                                pyautogui.moveTo(x, y)
                                pyautogui.click()
                                logger.info("Clique em 'restaurar' realizado.")
                    except Exception:
                        pass
                elif nome_modulo.upper() == "COBRANÇA BANCÁRIA 3.0":
                    limpar_restauracao_edge()
                    # Para COBRANÇA BANCÁRIA 3.0, procurar por navegador com a aba
                    win_modulo = get_browser_with_tab("Cobrança Bancária", timeout=15)
                    # Maximizar a janela (sem fullscreen)
                    win_modulo.maximize()
                    # Tentar clicar em 'restaurar'
                    try:
                        restaurar_img = base_ocr / "restaurar.png"
                        if restaurar_img.exists():
                            result = get_position_img(restaurar_img, threshold=0.8, timeout=3)
                            if result:
                                _, (x, y) = result
                                pyautogui.moveTo(x, y)
                                pyautogui.click()
                                logger.info("Clique em 'restaurar' realizado.")
                    except Exception:
                        pass
                else:
                    # Para outros módulos, usar a verificação padrão
                    win_modulo = get_window_by_title(
                        titulo=nome_modulo.upper(), 
                        app=win_principal.app, 
                        timeout=15
                    )
                
                try:
                    win_thread = threading.Thread(target=lambda: win_modulo.set_focus())
                    win_thread.daemon = True
                    win_thread.start()
                    win_thread.join(1.0)
                    logger.info("Foco transferido para a janela do Sisbr.")
                except Exception:
                    logger.error("Erro ao transferir o foco para a janela do Sisbr.")
                    pass
                logger.success(f"Módulo '{nome_modulo}' acessado com sucesso!")
                return win_modulo

            except Exception as e:
                if "Nenhum Edit encontrado" in str(e):
                    logger.error(f"Erro crítico ao localizar campo do módulo '{nome_modulo}': {e}")
                    raise
                logger.warning(f"Falha na tentativa {tentativa} de abrir o módulo '{nome_modulo}': {e}")
                if tentativa < max_retentativas:
                    time.sleep(3)
                else:
                    logger.error(f"Falha final ao abrir o módulo '{nome_modulo}'.")
                    raise RuntimeError(f"Não foi possível abrir o módulo '{nome_modulo}'")
    except Exception as e:
        logger.error(f"Falha final ao abrir o módulo '{nome_modulo}'.")
        raise RuntimeError(f"Não foi possível abrir o módulo '{nome_modulo}'")