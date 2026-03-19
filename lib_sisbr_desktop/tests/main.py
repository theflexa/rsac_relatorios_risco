# C:\Automations\lib_sisbr_desktop\tests\test_plataforma_atendimento.py
import sys
import argparse
import traceback
import time
import pyautogui
from pathlib import Path
from dotenv import load_dotenv
import os
import psutil

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, os.path.abspath(os.path.join(project_root, '../bot_agent/src')))

from loguru import logger
from datetime import datetime
from dateutil.relativedelta import relativedelta
from src.lib_sisbr_desktop.core.abrir_sisbr import abrir_sisbr
from src.lib_sisbr_desktop.core.login import login
from src.lib_sisbr_desktop.core.acessar_modulo import acessar_modulo
from src.lib_sisbr_desktop.core.trocar_cooperativa import trocar_cooperativa
from src.lib_sisbr_desktop.utils.status import is_logado
from src.lib_sisbr_desktop.utils.error_handler import error_handler
from src.lib_sisbr_desktop.utils.retry import retry
from src.lib_sisbr_desktop.utils.identificador import tipo_documento
from src.lib_sisbr_desktop.utils.extrair_avalistas import extrair_garantias
from src.lib_sisbr_desktop.utils.window import fechar_modulo

# Imports dos módulos de processo específicos
from tests.etapa_downloads import baixar_relatorio_serasa, baixar_relatorio_bacen, baixar_relatorio_faturamento_renda, baixar_relatorio_conta_corrente, fechar_popup_ia, baixar_relatorio_painel_comercial, baixar_relatorio_lancamentos, baixar_sumula_credito, baixar_relatorio_carteira_cadente, baixar_relatorio_liquidacoes_baixas, baixar_relatorio_liquidacoes_slc, baixar_docs_gerais_proposta, baixar_documentos_garantia
from tests.upload_sharepoint import upload_lote_para_link_sharepoint
from database import get_item_by_id

def setup_logging(cpf_cnpj: str):
    # Habilita cores ANSI no Windows
    import os
    if os.name == 'nt':
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        except:
            pass
    
    # Remove todos os handlers existentes
    logger.remove()
    
    # Formato colorido para console
    log_format = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}:{function}:{line}</cyan> - <level>{message}</level>"
    
    # Handler para console com cores
    logger.add(sys.stdout, level="INFO", format=log_format, colorize=True, backtrace=True, diagnose=True)
    
    # Handler para arquivo específico do teste
    log_file = project_root / f"logs/teste_plataforma_atendimento_doc_{cpf_cnpj}.log"
    log_file.parent.mkdir(exist_ok=True)
    logger.add(log_file, level="DEBUG", rotation="5 MB", format=log_format)
    
    logger.info(f"Logging configurado. Log: {log_file}")

def fechar_todas_instancias_sisbr():
    for proc in psutil.process_iter(['pid', 'name']):
        if 'sisbr' in proc.info['name'].lower():
            try:
                proc.kill()
                logger.info(f"Processo Sisbr (PID: {proc.info['pid']}) encerrado.")
            except Exception as e:
                logger.warning(f"Erro ao encerrar processo Sisbr: {e}")

@retry(times=3, delay_s=2)
def main_test_plataforma_atendimento(cpf_cnpj: str, id_item_teste: str, proposta: str, cooperativa, produto: str):
    logger.info(f"--- INICIANDO BAIXA DE RELATÓRIOS (Doc: {cpf_cnpj}) ---")
    
    PASTA_RELATORIOS_FINAL = str(project_root / "temp/relatorios_finais")
    NOME_MODULO = "PLATAFORMA DE ATENDIMENTO"
    CORTE_BACEN = 18
    hoje = datetime.now()
    data_bacen = (hoje + relativedelta(months= -2 if hoje.day < CORTE_BACEN else -1)).strftime("%Y-%m")
    app = None
    tipo_doc = tipo_documento(cpf_cnpj)
    
    # Carrega variáveis do .env para pegar o link compartilhado
    dotenv_path = os.getenv('UPLOAD_SHAREPOINT_ENV_PATH') or os.path.join(project_root, '.env')
    load_dotenv(dotenv_path)
    share_link = os.getenv("SHAREPOINT_SHARE_LINK")
    if not share_link:
        raise RuntimeError("A variável SHAREPOINT_SHARE_LINK não está definida no .env!")

    try:
        # ================================================
        # INIT APPLICATIONS
        # ================================================
        logger.info("Abrindo e fazendo login no Sisbr...")
        app, win_principal = abrir_sisbr()
        if not is_logado(win_principal):
            if not login(): raise RuntimeError("Falha no login.")
        time.sleep(10)
        
        logger.info("Trocar cooperativa...")
        trocar_cooperativa(win_principal,cooperativa)

        logger.info(f"Acessando o módulo '{NOME_MODULO}'...")
        win_atendimento = acessar_modulo(win_principal, NOME_MODULO,5)
        if not win_atendimento:
            raise RuntimeError(f"Falha ao obter a janela do módulo '{NOME_MODULO}'.")
        time.sleep(3)

        # Fechar pop-up da IA se presente
        fechar_popup_ia()

        # ================================================
        # DOWNLOAD SERASA
        # ================================================

        logger.info("Baixando relatório SERASA...")
        caminho_serasa = baixar_relatorio_serasa(win_atendimento, id_item_teste, PASTA_RELATORIOS_FINAL, cpf_cnpj, tipo_doc)
        logger.info(f"Relatório SERASA salvo em: {caminho_serasa}")
        
        # ================================================
        # DOWNLOAD BACEN
        # ================================================

        logger.info("Baixando relatório BACEN...")
        caminho_bacen = baixar_relatorio_bacen(win_atendimento, id_item_teste, PASTA_RELATORIOS_FINAL, data_bacen, cpf_cnpj)
        logger.info(f"Relatório BACEN salvo em: {caminho_bacen}")

        # ================================================
        # DOWNLOAD FATURAMENTO/RENDA
        # ================================================

        logger.info("Baixando relatório FATURAMENTO/RENDA...")
        caminhos_faturamento = baixar_relatorio_faturamento_renda(win_atendimento, id_item_teste, PASTA_RELATORIOS_FINAL, cpf_cnpj, cooperativa, tipo_doc)
        logger.info(f"Relatórios FATURAMENTO/RENDA salvos em: {caminhos_faturamento}")
        
        # ================================================
        # DOWNLOAD CONTA CORRENTE
        # ================================================

        logger.info("Baixando relatório CONTA CORRENTE...")
        caminho_conta_corrente = baixar_relatorio_conta_corrente(win_atendimento, id_item_teste, PASTA_RELATORIOS_FINAL, cpf_cnpj)
        logger.info(f"Relatório CONTA CORRENTE salvo em: {caminho_conta_corrente}")

        # ================================================
        # DOWNLOAD SÚMULA DE CRÉDITO
        # ================================================

        logger.info("Baixando SÚMULA DE CRÉDITO...")
        caminho_sumula = baixar_sumula_credito(win_principal, id_item_teste, PASTA_RELATORIOS_FINAL, proposta, produto)
        logger.info(f"SÚMULA DE CRÉDITO salva em: {caminho_sumula}")
        dados_sumula = extrair_garantias(caminho_sumula)
        # Usar os CPFs/CNPJs já extraídos pela função extrair_garantias
        cpfs_avalistas = dados_sumula.get('cpfs_avalistas', [])
        cpfs_grupo_economico = dados_sumula.get('cpfs_grupo_economico', [])
        numero_conta = dados_sumula.get('numero_conta')
        associado_desde = dados_sumula.get('associado_desde')
        logger.info(f"CPFs Avalistas: {cpfs_avalistas}")
        logger.info(f"CPFs Grupo Econômico: {cpfs_grupo_economico}")
        logger.info(f"Número da conta: {numero_conta}")
        logger.info(f"Associado desde: {associado_desde}")

        # ================================================
        # DOWNLOAD PAINEL COMERCIAL
        # ================================================

        logger.info("Baixando relatórios do PAINEL COMERCIAL...")
        caminhos_painel_comercial = baixar_relatorio_painel_comercial(win_principal, id_item_teste, PASTA_RELATORIOS_FINAL, cpf_cnpj)
        logger.info(f"Relatórios do PAINEL COMERCIAL salvos em: {caminhos_painel_comercial}")

        # ================================================
        # DOWNLOAD LANÇAMENTOS
        # ================================================

        logger.info("Baixando relatório de LANÇAMENTOS...")
        caminho_lancamentos = baixar_relatorio_lancamentos(win_principal, id_item_teste, PASTA_RELATORIOS_FINAL, cpf_cnpj, numero_conta)
        logger.info(f"Relatório de LANÇAMENTOS salvo em: {caminho_lancamentos}")

        # ================================================
        # DOWNLOAD CARTEIRA CADENTE
        # ================================================
        
        logger.info("Baixando relatório da CARTEIRA CADENTE...")
        caminho_carteira_cadente = baixar_relatorio_carteira_cadente(win_principal, id_item_teste, PASTA_RELATORIOS_FINAL, associado_desde, cpf_cnpj, produto)
        logger.info(f"Relatório da CARTEIRA CADENTE salvo em: {caminho_carteira_cadente}")

        # ================================================
        # DOWNLOAD LIQUIDAÇÕES BAIXAS
        # ================================================
        
        logger.info("Baixando relatório de LIQUIDAÇÕES BAIXAS...")
        caminho_liquidacoes_baixas = baixar_relatorio_liquidacoes_baixas(win_principal, id_item_teste, PASTA_RELATORIOS_FINAL, cpf_cnpj)
        logger.info(f"Relatório de LIQUIDAÇÕES BAIXAS salvo em: {caminho_liquidacoes_baixas}")

        # ================================================
        # DOWNLOAD LIQUIDAÇÕES SLC
        # ================================================
        
        logger.info("Baixando relatório de LIQUIDAÇÕES SLC...")
        caminho_liquidacoes_slcs = baixar_relatorio_liquidacoes_slc(win_principal, id_item_teste, PASTA_RELATORIOS_FINAL, cpf_cnpj)
        logger.info(f"Relatório de LIQUIDAÇÕES SLC salvo em: {caminho_liquidacoes_slcs}")
        
        # ================================================
        # DOWNLOAD DOCS GERAIS
        # ================================================

        logger.info("Baixando relatório de DOCS GERAIS...")
        caminho_docs_gerais = baixar_docs_gerais_proposta(win_principal, id_item_teste, PASTA_RELATORIOS_FINAL, produto, proposta)
        logger.info(f"Relatório de DOCS GERAIS salvo em: {caminho_docs_gerais}")

        # ================================================
        # DOWNLOAD GARANTIAS
        # ================================================

        logger.info("Baixando relatório de GARANTIAS...")
        caminho_garantias = baixar_documentos_garantia(win_principal, id_item_teste, PASTA_RELATORIOS_FINAL, produto, proposta)
        logger.info(f"Relatório de GARANTIAS salvo em: {caminho_garantias}")

        # ================================================
        # ================================================

        relatorios = [caminho_serasa, caminho_bacen] + list(caminhos_faturamento.values()) + list(caminho_conta_corrente.values()) + list(caminhos_painel_comercial.values()) + [caminho_lancamentos, caminho_sumula, caminho_carteira_cadente, caminho_liquidacoes_baixas]
        logger.success("--- TESTE DA PLATAFORMA DE ATENDIMENTO CONCLUÍDO COM SUCESSO ---")
        
        # ================= UPLOAD PARA SHAREPOINT POR CPF (via link compartilhado) =====================
        nome_subpasta = f"{cooperativa}_{proposta}_{cpf_cnpj}"
        logger.info(f"Iniciando upload dos relatórios para o SharePoint (via link) na subpasta: {nome_subpasta}")
        pasta_url = upload_lote_para_link_sharepoint(relatorios, share_link, nome_subpasta)
        logger.info(f"Upload dos relatórios do CPF {cpf_cnpj} finalizado! Acesse: {pasta_url}")
        # =====================================================================

    except Exception as e:
        logger.error(f"Ocorreu um erro durante o teste: {e}")
        logger.error(traceback.format_exc())
        screenshot_path = project_root / f"logs/error_screenshot_atendimento_{cpf_cnpj}.png"
        pyautogui.screenshot(str(screenshot_path))
        logger.error(f"Screenshot do erro salvo em: {screenshot_path}")
        logger.critical("--- TESTE DA PLATAFORMA DE ATENDIMENTO FALHOU ---")
        if 'win_atendimento' in locals():
            error_handler(win_atendimento)
        fechar_todas_instancias_sisbr()
        raise
    finally:
        logger.info("Finalizando script de teste.")

def main_loop():
    while True:
        try:
            main_test_plataforma_atendimento(cpf_cnpj, item_id, proposta, cooperativa, produto)
            break  # Sai do loop se rodar com sucesso
        except Exception as e:
            logger.critical(f"Erro fatal detectado: {e}")
            fechar_todas_instancias_sisbr()
            logger.info("Aguardando 10 segundos antes de reiniciar o processo...")
            time.sleep(10)
            logger.info("Reiniciando o processo do zero...")

if __name__ == "__main__":
    # parser = argparse.ArgumentParser(description="Script de teste para a Plataforma de Atendimento no Sisbr.")
    # parser.add_argument("--item-id", required=True, help="ID do item no banco de dados.")
    # args = parser.parse_args()
    # item_id = args.item_id
    item_id = "145839"
    logger.info(f"Buscando item no banco com id={item_id}...")
    item = get_item_by_id(item_id)
    if not item:
        logger.error(f"Item com id {item_id} não encontrado.")
        sys.exit(1)
    logger.success(f"Item encontrado: {item}")
    dados = item.get("data", {})
    cpf_cnpj = dados.get("cpf_cnpj")
    proposta = dados.get("proposta")
    cooperativa = dados.get("cooperativa")
    produto = dados.get("produto")
    
    setup_logging(cpf_cnpj)
    logger.info("Iniciando main_test_plataforma_atendimento...")
    main_loop()