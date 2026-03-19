from functools import wraps
from loguru import logger
from typing import Callable, Any, TypeVar, Tuple

T = TypeVar('T')

def reiniciar_em_caso_de_popup(max_tentativas: int = 3):
    """
    Decorador que reinicia a função se um popup for detectado.
    
    Args:
        max_tentativas: Número máximo de tentativas antes de desistir
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(win_modulo, *args, **kwargs) -> T:
            tentativas = 0
            ultima_excecao = None
            
            while tentativas < max_tentativas:
                try:
                    return func(win_modulo, *args, **kwargs)
                except Exception as e:
                    tentativas += 1
                    ultima_exc = e
                    
                    logger.warning(f"Tentativa {tentativas}/{max_tentativas} falhou: {e}")
                    
                    # Se for a última tentativa, não tenta mais
                    if tentativas >= max_tentativas:
                        logger.error(f"Número máximo de tentativas ({max_tentativas}) atingido")
                        raise ultima_exc from e
                    
                    # Tenta tratar o erro (fechar popups, etc)
                    try:
                        from .error_handler import error_handler
                        logger.info("Tentando fechar popups...")
                        error_handler(win_modulo)
                    except Exception as handler_error:
                        logger.error(f"Erro ao tentar fechar popups: {handler_error}")
                    
                    # Pequena pausa antes de tentar novamente
                    import time
                    time.sleep(2)
        
        return wrapper
    return decorator
