import os
import sys
from loguru import logger

# Habilita cores ANSI no Windows
if os.name == 'nt':
    # Tenta habilitar cores ANSI no Windows
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except:
        pass

# Remove handlers padrão para evitar conflitos
logger.remove()

# Formato colorido para logs
log_format = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}:{function}:{line}</cyan> - <level>{message}</level>"

# Adiciona handler para arquivo com formatação completa
logger.add("logs/sisbr.log", rotation="500 KB", retention="10 days", encoding="utf-8", format=log_format, level="DEBUG")

# Adiciona handler para console com cores
# Usa sys.stdout em vez de lambda para melhor compatibilidade
logger.add(sys.stdout, level="INFO", format=log_format, colorize=True, backtrace=True, diagnose=True)
