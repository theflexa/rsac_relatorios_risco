import time
from functools import wraps
from loguru import logger

def retry(times: int, delay_s: float = 1.0):
    def decorator(func):
        
        @wraps(func)
        
        def wrapper(*args, **kwargs):
            logger.info(f"Iniciando tentativas de {func.__name__}...")
            for attempt in range(1, times + 1):
                try:
                    logger.info(f"Tentativa {attempt}/{times}...")
                    return func(*args, **kwargs)
                except Exception as e:
                    logger.warning(f"Tentativa {attempt}/{times} falhou: {e}")
                    if attempt == times:
                        raise
                    time.sleep(delay_s)
        return wrapper
    return decorator
