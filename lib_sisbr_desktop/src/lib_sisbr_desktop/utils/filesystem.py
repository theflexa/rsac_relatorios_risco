# src/lib_sisbr_desktop/utils/filesystem.py
import os
import time
from pathlib import Path
from loguru import logger

def aguardar_download(pasta_download: str, extensao: str, timeout: int = 60) -> str | None:
    """
    Aguarda um novo arquivo com a extensão especificada aparecer em uma pasta.
    Retorna o caminho completo do arquivo ou None se o timeout for atingido.
    """
    pasta = Path(pasta_download)
    tempo_inicial = time.time()
    arquivos_iniciais = set(p.name for p in pasta.glob(f"*.{extensao}"))
    
    logger.info(f"Aguardando novo arquivo '.{extensao}' na pasta: {pasta}")
    
    while time.time() - tempo_inicial < timeout:
        arquivos_atuais = set(p.name for p in pasta.glob(f"*.{extensao}"))
        novos_arquivos = arquivos_atuais - arquivos_iniciais
        
        if novos_arquivos:
            nome_novo_arquivo = novos_arquivos.pop()
            caminho_completo = str(pasta / nome_novo_arquivo)
            logger.success(f"Download concluído: {caminho_completo}")
            return caminho_completo
            
        time.sleep(1)
        
    logger.error(f"Timeout de {timeout}s atingido. Nenhum novo arquivo '.{extensao}' foi encontrado.")
    return None