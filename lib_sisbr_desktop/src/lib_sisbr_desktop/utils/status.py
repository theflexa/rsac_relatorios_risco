from .window import get_window_by_title

def is_logado(win) -> bool:
    """
    Verifica se o Sisbr está logado com base na presença do elemento "MENU DE APLICATIVOS SISBR".
    """
    try:
        elementos = win.descendants(title="MENU DE APLICATIVOS SISBR", control_type="Text")
        return len(elementos) > 0
    except:
        return False

def is_modulo_aberto(nome_modulo: str, app) -> bool:
    try:
        get_window_by_title(nome_modulo.upper(), app)
        return True
    except:
        return False