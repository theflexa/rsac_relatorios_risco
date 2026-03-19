# src/lib_sisbr_desktop/utils/wait.py
from pywinauto.timings import wait_until, TimeoutError
from pywinauto.base_wrapper import BaseWrapper
from loguru import logger

def wait_for_element(win_or_element, timeout: int = 30, retry_interval: float = 1.0, **kwargs) -> BaseWrapper:
    """
    Aguarda de forma inteligente até que um elemento descendente apareça.
    """
    criterios_str = ", ".join([f"{k}='{v}'" for k, v in kwargs.items()])
    logger.debug(f"Aguardando elemento descendente com critérios: {criterios_str} por até {timeout}s.")

    elemento_encontrado = None

    def _find_descendant():
        nonlocal elemento_encontrado
        try:
            elementos = win_or_element.descendants(**kwargs)
            if elementos:
                elemento_encontrado = elementos[0]
                return True
        except Exception:
            pass
        return False

    try:
        wait_until(timeout=timeout, retry_interval=retry_interval, func=_find_descendant)
        logger.success(f"Elemento descendente encontrado: {criterios_str}")
        return elemento_encontrado
    except TimeoutError:
        logger.error(f"Timeout: Elemento com critérios [{criterios_str}] não apareceu em {timeout}s.")
        raise TimeoutError(f"Elemento com critérios [{criterios_str}] não apareceu em {timeout}s.")