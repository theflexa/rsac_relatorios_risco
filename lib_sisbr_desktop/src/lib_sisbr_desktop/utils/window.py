from pywinauto.application import Application
from pywinauto.keyboard import send_keys
from ..gui.mapeamento import POPUPS_GERAIS
from loguru import logger
import time
import psutil
import pyautogui

def get_window_by_title(titulo: str, app: Application, timeout: int = 15, match_case: bool = False):
    """
    Retorna a janela com o título informado, aguardando por um tempo.
    """
    end_time = time.time() + timeout
    while time.time() < end_time:
        for win in app.windows():
            titulo_atual = win.window_text().strip()
            if (match_case and titulo_atual == titulo) or \
               (not match_case and titulo_atual.upper() == titulo.upper()):
                return win
        time.sleep(0.5)
    raise TimeoutError(f"Janela com o título '{titulo}' não foi encontrada em {timeout}s.")


def get_browser_with_tab(tab_title: str, timeout: int = 15):
    """
    Detecta se há um navegador (Chrome ou Edge) aberto com a aba especificada.
    Retorna a janela do navegador se encontrada.
    """
    logger.info(f"Procurando por navegador com aba '{tab_title}'...")
    
    end_time = time.time() + timeout
    while time.time() < end_time:
        try:
            # Procurar por processos do Chrome
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'].lower() in ['chrome.exe', 'msedge.exe']:
                    try:
                        # Tentar conectar ao processo do navegador
                        app = Application(backend="uia").connect(process=proc.info['pid'])
                        for win in app.windows():
                            titulo_atual = win.window_text().strip()
                            # Verificar se o título contém o nome da aba
                            if tab_title.upper() in titulo_atual.upper() or titulo_atual.upper() in tab_title.upper():
                                logger.success(f"Navegador encontrado com aba '{tab_title}': {titulo_atual}")
                                return win
                    except Exception as e:
                        # Se não conseguir conectar, continua para o próximo processo
                        continue
        except Exception as e:
            logger.debug(f"Erro ao verificar processos: {e}")
        
        time.sleep(0.5)
    
    raise TimeoutError(f"Navegador com aba '{tab_title}' não foi encontrado em {timeout}s.")


def limpar_popups_comuns(win, max_loops=5, delay_entre_loops=1):
    """
    Fecha pop-ups e alertas comuns que podem travar a automação.
    Replica a lógica de limpeza de ambiente (ConfigAmbiente.xaml).
    """
    logger.info("Verificando e limpando pop-ups comuns...")
    for i in range(max_loops):
        popup_encontrado = False
        
        # Tenta fechar o botão "FECHAR" de pop-ups de erro
        try:
            fechar_btn = win.child_window(**POPUPS_GERAIS["fechar_button"])
            if fechar_btn.exists():
                logger.warning("Pop-up 'FECHAR' encontrado. Tentando fechar.")
                fechar_btn.click_input()
                popup_encontrado = True
                time.sleep(0.5)
        except Exception:
            pass

        # Tenta fechar o botão "OK" de alertas
        try:
            ok_btn = win.child_window(**POPUPS_GERAIS["ok_button"])
            if ok_btn.exists():
                logger.warning("Pop-up 'OK' encontrado. Tentando fechar.")
                ok_btn.click_input()
                popup_encontrado = True
                time.sleep(0.5)
        except Exception:
            pass
            
        # Se nenhum pop-up foi encontrado neste loop, podemos sair.
        if not popup_encontrado:
            logger.info("Nenhum pop-up comum encontrado para limpar.")
            return True
            
        logger.info(f"Loop de limpeza de pop-up {i+1}/{max_loops}. Aguardando...")
        time.sleep(delay_entre_loops)

    logger.warning("Máximo de tentativas de limpeza de pop-ups atingido.")
    return False


def fechar_modulo(win_principal, titulo_modulo: str, timeout: int = 3) -> bool:
    """Fecha a janela/aba de um módulo pelo título informado.

    - Tenta como janela do aplicativo (UIA)
    - Se não encontrar, tenta como aba de navegador (Chrome/Edge)
    - Fecha com close(); se falhar, usa Alt+F4

    Retorna True se encontrou e fechou; False se não estava aberta.
    """
    win_modulo = None

    # 1) Tenta localizar como janela do aplicativo
    try:
        win_modulo = get_window_by_title(
            titulo=titulo_modulo,
            app=win_principal.app,
            timeout=timeout
        )
    except Exception:
        win_modulo = None

    # 2) Se não encontrou, tenta como aba do navegador (Chrome/Edge)
    if win_modulo is None:
        try:
            win_modulo = get_browser_with_tab(tab_title=titulo_modulo, timeout=timeout)
        except Exception:
            logger.info(f"Módulo/aba '{titulo_modulo}' não está aberto(a).")
            return False

    # 3) Fechar a janela/aba encontrada
    try:
        try:
            win_modulo.set_focus()
        except Exception:
            pass

        try:
            win_modulo.close()
            logger.success(f"'{titulo_modulo}' fechado com sucesso (close()).")
            return True
        except Exception:
            send_keys('%{F4}')  # Alt+F4
            time.sleep(0.3)
            logger.success(f"'{titulo_modulo}' fechado com Alt+F4.")
            return True
    except Exception as e:
        logger.warning(f"Falha ao fechar '{titulo_modulo}': {e}. Tentando fallback final...")
        try:
            pyautogui.hotkey('alt', 'f4')
            time.sleep(0.3)
            logger.success(f"'{titulo_modulo}' fechado no fallback final.")
            return True
        except Exception as eh:
            logger.error(f"Não foi possível fechar '{titulo_modulo}': {eh}")
            return False