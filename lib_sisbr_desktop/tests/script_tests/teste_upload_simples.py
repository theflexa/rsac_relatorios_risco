import sys
import os
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Carregar variáveis do .env
load_dotenv()

# Importar função real do upload_sharepoint
from tests.upload_sharepoint import upload_lote_para_link_sharepoint

def testar_upload_simples():
    """
    Script simples para testar upload usando as funções reais e credenciais do .env
    """
    logger.info("Iniciando teste simples de upload para o SharePoint...")
    
    try:
        # Verificar se as variáveis de ambiente estão definidas
        share_link = os.getenv("SHAREPOINT_SHARE_LINK")
        if not share_link:
            raise ValueError("SHAREPOINT_SHARE_LINK não está definida no .env")
        
        # Procurar por arquivos na pasta temp/relatorios_finais
        pasta_temp = project_root / "temp" / "relatorios_finais"
        if not pasta_temp.exists():
            logger.warning(f"Pasta {pasta_temp} não existe. Criando pasta vazia...")
            pasta_temp.mkdir(parents=True, exist_ok=True)
            
            # Criar um arquivo de teste
            arquivo_teste = pasta_temp / "arquivo_teste.txt"
            with open(arquivo_teste, "w", encoding="utf-8") as f:
                f.write("Arquivo de teste para upload do SharePoint\n")
                f.write(f"Criado em: {os.path.basename(__file__)}\n")
        
        # Listar arquivos disponíveis
        arquivos = list(pasta_temp.glob("*"))
        if not arquivos:
            raise ValueError(f"Nenhum arquivo encontrado em {pasta_temp}")
        
        # Pegar o primeiro arquivo encontrado
        arquivo_teste = arquivos[0]
        logger.info(f"Usando arquivo: {arquivo_teste.name}")
        
        # Nome da subpasta de teste
        nome_subpasta = "teste_upload_simples"
        
        # Fazer upload usando a função real
        logger.info(f"Fazendo upload do arquivo '{arquivo_teste.name}' para subpasta '{nome_subpasta}'...")
        
        resultado = upload_lote_para_link_sharepoint(
            lista_arquivos=[str(arquivo_teste)],
            share_link=share_link,
            nome_subpasta=nome_subpasta
        )
        
        logger.success("Upload realizado com sucesso!")
        logger.info(f"Resultado: {resultado}")
        
        return True
        
    except Exception as e:
        logger.error(f"Erro durante o teste: {e}")
        return False

if __name__ == "__main__":
    # Configurar logging
    logger.remove()
    logger.add(sys.stderr, level="INFO", format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>")
    
    # Executar teste
    sucesso = testar_upload_simples()
    
    if sucesso:
        logger.success("Teste executado com sucesso!")
    else:
        logger.error("Teste falhou!")
        sys.exit(1)