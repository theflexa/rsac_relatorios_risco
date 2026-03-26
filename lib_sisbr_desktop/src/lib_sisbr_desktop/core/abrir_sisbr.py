# src/lib_sisbr_desktop/core/abrir_sisbr.py
import os
import time
from pywinauto.application import Application
from ..config import SISBR_EXE
from loguru import logger


def _is_usable_main_window(win) -> bool:
    try:
        if not win.exists():
            return False
        if not win.is_visible():
            return False
        rect = win.rectangle()
        width = rect.right - rect.left
        height = rect.bottom - rect.top
        if width <= 0 or height <= 0:
            return False
        if rect.left <= -30000 or rect.top <= -30000:
            return False
        return True
    except Exception:
        return False


def _wait_for_usable_window(win, *, timeout: int, retry_delay: float = 0.5) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            win.wait("exists visible ready", timeout=1)
        except Exception:
            time.sleep(retry_delay)
            continue
        if _is_usable_main_window(win):
            return True
        time.sleep(retry_delay)
    return False


def abrir_sisbr(caminho_exe: str = SISBR_EXE, timeout: int = 30):
    """
    Inicia o Sisbr 2.0 se não estiver aberto, ou conecta-se a uma instância existente.
    Usa o backend 'uia' que é o mais confiável para encontrar a janela principal.
    Retorna a tupla (app, win_principal).
    """
    logger.info("Verificando se o Sisbr 2.0 já está em execução para conectar...")
    print(caminho_exe)
    if not caminho_exe or not os.path.exists(caminho_exe):
        raise FileNotFoundError(f"Executável do Sisbr não encontrado no caminho especificado: {caminho_exe}")

    app = None
    win_principal = None

    try:
        # Tenta CONECTAR a uma instância já aberta usando o backend 'uia'
        # Usamos um timeout mais curto para a conexão, pois deve ser rápido se a janela existir.
        app = Application(backend="uia").connect(title_re="Sisbr 2.0", timeout=10)
        win_principal = app.window(title_re="Sisbr 2.0")
        if not _wait_for_usable_window(win_principal, timeout=5):
            raise RuntimeError("Janela conectada do Sisbr está em estado fantasma/off-screen.")
        logger.success("Conectado a uma instância existente do Sisbr 2.0.")

    except Exception as connection_error:
        logger.warning(
            f"Nenhuma instância utilizável do Sisbr 2.0 foi encontrada ({connection_error}). Iniciando uma nova..."
        )
        try:
            # Se a conexão falhar, tenta INICIAR uma nova aplicação
            app = Application(backend="uia").start(cmd_line=f'"{caminho_exe}"')
            
            # Aguarda a janela principal aparecer com um timeout mais longo
            win_principal = app.window(title_re="Sisbr 2.0")
            if not _wait_for_usable_window(win_principal, timeout=timeout):
                raise RuntimeError("A nova instância do Sisbr abriu sem uma janela principal utilizável.")
            logger.success("Nova instância do Sisbr 2.0 iniciada com sucesso.")
            
        except Exception as e:
            logger.error(f"Falha crítica ao tentar iniciar o Sisbr 2.0: {e}")
            raise RuntimeError(f"Não foi possível iniciar o Sisbr 2.0 a partir de '{caminho_exe}'.") from e

    # Garante que a janela esteja pronta para interação
    if win_principal and _wait_for_usable_window(win_principal, timeout=10):
        if win_principal.is_minimized():
            win_principal.restore()
        
        win_principal.set_focus()
        win_principal.maximize()
        logger.info("Janela do Sisbr está em foco e pronta para uso.")
    else:
        raise RuntimeError("Não foi possível obter um handle válido para a janela principal do Sisbr.")

    return app, win_principal
