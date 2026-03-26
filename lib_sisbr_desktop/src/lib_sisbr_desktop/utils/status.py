import time

from loguru import logger

from .window import get_window_by_title


UPDATE_MESSAGE = "EFETUANDO DOWNLOAD DA ATUALIZAÇÃO!"
MENU_LOADING_MESSAGE = "CARREGANDO MENU DE APLICATIVOS"
WAIT_MESSAGE = "AGUARDE!"
CONNECTIVITY_ERROR_MESSAGE = (
    "Não foi possível efetuar conexão aos servidores do Sicoob Confederação. "
    "Verifique a sua conexão de rede local na cooperativa ou o link de comunicação."
)
RESTART_MESSAGE = "REINICIAR AGORA!"
IO_ERROR_TITLE = "IO ERROR!"


def _has_named_descendant(win, name: str) -> bool:
    try:
        for elem in win.descendants():
            try:
                if elem.element_info.name == name:
                    return True
            except Exception:
                continue
    except Exception:
        pass

    for control_type in ("Text", "Edit", "Button"):
        try:
            elementos = win.descendants(title=name, control_type=control_type)
            if elementos:
                return True
        except Exception:
            continue
    return False


def _has_module_search_field(win) -> bool:
    try:
        for edit in win.descendants(control_type="Edit"):
            try:
                r = edit.rectangle()
                if (
                    abs(r.left - 29) <= 15 and
                    abs(r.top - 990) <= 15 and
                    abs(r.right - 258) <= 2 and
                    abs(r.bottom - 1009) <= 15
                ):
                    return True
            except Exception:
                continue
    except Exception:
        return False
    return False

def is_logado(win) -> bool:
    """
    Verifica se o Sisbr está logado com base em marcadores da tela principal.
    """
    try:
        return (
            _has_named_descendant(win, "MENU DE APLICATIVOS SISBR")
            or _has_module_search_field(win)
            or _has_named_descendant(win, "NOVA COOPERATIVA:")
        )
    except Exception:
        return False


def is_updating(win) -> bool:
    try:
        return _has_named_descendant(win, UPDATE_MESSAGE)
    except Exception:
        return False


def is_loading_menu(win) -> bool:
    try:
        return _has_named_descendant(win, MENU_LOADING_MESSAGE) or _has_named_descendant(win, WAIT_MESSAGE)
    except Exception:
        return False


def has_connectivity_error(win) -> bool:
    try:
        return _has_named_descendant(win, CONNECTIVITY_ERROR_MESSAGE)
    except Exception:
        return False


def wait_until_ready(win, timeout: float = 120.0, retry_delay: float = 1.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if is_logado(win) and not is_loading_menu(win):
            return True
        if has_connectivity_error(win):
            return False
        time.sleep(retry_delay)
    return False

def has_restart_prompt(win) -> bool:
    """Verifica se o Sisbr está exibindo a tela de 'REINICIAR AGORA!'."""
    try:
        return _has_named_descendant(win, RESTART_MESSAGE)
    except Exception:
        return False


def click_restart_button(win) -> bool:
    """Clica no botão 'REINICIAR AGORA!' se presente."""
    try:
        for elem in win.descendants():
            try:
                if elem.element_info.name == RESTART_MESSAGE:
                    elem.click_input()
                    logger.info("[Status] Botão 'REINICIAR AGORA!' clicado.")
                    return True
            except Exception:
                continue
    except Exception:
        pass
    return False


def has_io_error(win) -> bool:
    """Verifica se a janela de IO ERROR! está presente (erro de inicialização)."""
    try:
        return _has_named_descendant(win, IO_ERROR_TITLE) or _has_named_descendant(
            win, CONNECTIVITY_ERROR_MESSAGE
        )
    except Exception:
        return False


def is_modulo_aberto(nome_modulo: str, app) -> bool:
    try:
        get_window_by_title(nome_modulo.upper(), app)
        return True
    except:
        return False
