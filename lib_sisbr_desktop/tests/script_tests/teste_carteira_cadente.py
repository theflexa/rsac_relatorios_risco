# Imports padrão do Python
import sys
import time
import os
import re
from pathlib import Path
from datetime import datetime, timedelta

# Imports de terceiros
import pyautogui
from PIL import Image, ImageChops, ImageStat, ImageOps, ImageEnhance
from pywinauto import Application
from loguru import logger

# Configuração do path do projeto
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Imports internos do projeto
from src.lib_sisbr_desktop.gui.helpers import (
    verificar_campo_muda_de_cor, 
    double_click_coords, 
    get_position_img,
    click_and_verify,
    click_coords_and_verify,
    click_coords_and_verify_double,
    scroll_until_find_image
)
from src.lib_sisbr_desktop.gui.mapeamento import RETANGULOS_CONTACORRENTE_RECT, REGIAO_PRINT, PLATAFORMA_DE_CREDITO, COBRANCA_BANCARIA
from src.lib_sisbr_desktop.utils.screen_utils import salvar_print_regiao
from src.lib_sisbr_desktop.core.acessar_modulo import acessar_modulo
from src.lib_sisbr_desktop.gui.typer import write_with_retry, write_with_retry_formatted
from tests.plataforma_atendimento import acessa_submodulo

# Caminho dos templates
current_file = Path(__file__).resolve()
lib_project_root = current_file.parent.parent
ocr_path = (lib_project_root / "src" / "lib_sisbr_desktop" / "ocr" / "plataforma_de_atendimento").resolve()

# Variáveis globais necessárias
win_principal = None
produto = "FATURAMENTO/RENDA"  # ou outro produto conforme necessário


def baixar_relatorio_conta_corrente(win_modulo, id_item: str, pasta_destino_final: str, associado_desde: str, cpf_cnpj: str):
    """
    Executa o fluxo completo de download do relatório de Conta Corrente.
    """
    logger.info("Iniciando processo de download do relatório Conta Corrente.")
    win_modulo.set_focus()
    try:
        # Caminho dos templates de crédito
        ocr_cobranca = (lib_project_root / "src" / "lib_sisbr_desktop" / "ocr" / "cobranca_bancaria").resolve()
        
        # Organizar todas as imagens no começo da função com nomenclatura clara
        btn_boleto = ocr_cobranca / "boleto.png"
        btn_movimento = ocr_cobranca / "movimento_liquidacao.png"
        btn_beneficiario = ocr_cobranca / "beneficiario.png"
        btn_cpf_cnpj = ocr_cobranca / "cpf_cnpj.png"
        btn_inserir_cpf_cnpj = ocr_cobranca / "inserir_cpf_cnpj.png"
        btn_pesquisa = ocr_cobranca / "pesquisa.png"
        btn_filtro = ocr_cobranca / "filtro.png"
        btn_voltar = ocr_cobranca / "voltar.png"
        scroll = ocr_cobranca / "scroll.png"
        btn_liquidacao = ocr_cobranca / "liquidacao.png"
        btn_sintetico = ocr_cobranca / "sintetico.png"
        btn_pdf = ocr_cobranca / "pdf.png"
        btn_data_inicio = ocr_cobranca / "data_inicio.png"
        btn_data_termino = ocr_cobranca / "data_termino.png"
        btn_relatorio = ocr_cobranca / "relatorios.png"
        btn_impressora = ocr_cobranca / "impressora.png"
        btn_finalizado = ocr_cobranca / "finalizado.png"
        btn_nenhum_registro = ocr_cobranca / "nenhum_registro.png"
        btn_gerar_relatorio = ocr_cobranca / "gerar_relatorio.png"

        # Sequência de cliques e verificações usando click_and_verify
        logger.info("Iniciando sequência de cliques e verificações...")
        
        # boleto - relatorio
        logger.info("Clicando em boleto e verificando relatorio...")
        click_and_verify(btn_boleto, btn_relatorio)
        
        # relatorio - movimento
        logger.info("Clicando em relatorio e verificando movimento...")
        click_and_verify(btn_relatorio, btn_movimento)
        
        # movimento - beneficiario
        logger.info("Clicando em movimento e verificando beneficiario...")
        click_and_verify(btn_movimento, btn_beneficiario)
        
        # beneficiario - cpf_cnpj
        logger.info("Clicando em beneficiario e verificando cpf_cnpj...")
        click_and_verify(btn_beneficiario, btn_cpf_cnpj)
        
        # cpf_cnpj - pesquisa
        logger.info("Clicando em cpf_cnpj e verificando pesquisa...")
        click_and_verify(btn_cpf_cnpj, btn_pesquisa)
        
        # Inserir CPF/CNPJ antes de pesquisar
        logger.info(f"Inserindo CPF/CNPJ: {cpf_cnpj}")
        
        # Clicar no centro da imagem btn_inserir_cpf_cnpj
        logger.info("Clicando no campo para inserir CPF/CNPJ...")
        resultado_posicao = get_position_img(btn_inserir_cpf_cnpj, timeout=6)
        if not resultado_posicao:
            raise RuntimeError("Campo para inserir CPF/CNPJ não encontrado")
        
        # Extrair apenas as coordenadas (x, y) do resultado
        _, coordenadas = resultado_posicao
        pyautogui.click(coordenadas)
        time.sleep(0.5)
        
        # Inserir o CPF/CNPJ usando write_with_retry_formatted (aceita formatação automática)
        logger.info("Digitando CPF/CNPJ...")
        write_with_retry_formatted(
            x=coordenadas[0],
            y=coordenadas[1],
            expected_text=cpf_cnpj,
            retries=3,
            delay=0.2
        )
        
        # Verificar se o botão pesquisar ainda está visível após inserir o CPF/CNPJ
        click_and_verify(btn_pesquisa, btn_filtro)
        time.sleep(0.5)

        # Após este ponto: se houver "nenhum_registro", encerrar retornando None,
        # caso contrário, clicar nas coordenadas solicitadas e verificar o botão voltar
        logger.info("Verificando se há 'nenhum_registro'...")
        nenhum_registro_match = get_position_img(btn_nenhum_registro, timeout=3)
        if nenhum_registro_match:
            logger.info("Nenhum registro encontrado. Encerrando fluxo e retornando None.")
            return None
        else:
            logger.info("Registros encontrados. Clicando na região informada e verificando botão 'voltar'...")
            # Coordenadas do BoundingRectangle: {l:1171 t:352 r:1415 b:393}
            # Vamos clicar no centro deste retângulo
            left, top, right, bottom = 1171, 352, 1415, 393
            center_x = (left + right) // 2
            center_y = (top + bottom) // 2
            if not click_coords_and_verify_double((center_x, center_y), btn_voltar, verify_timeout=8):
                raise RuntimeError("Falha ao verificar o botão 'voltar' após clique nas coordenadas informadas.")
        
            # Inserir datas nos campos de data início e data término
            logger.info("Inserindo datas nos campos de data...")
            
            # Calcular datas: início (hoje - 90 dias) e término (hoje)
            data_hoje = datetime.now()
            data_inicio = data_hoje - timedelta(days=90)
            
            # Formatar datas para o padrão dd/mm/aaaa
            data_inicio_str = data_inicio.strftime("%d/%m/%Y")
            data_hoje_str = data_hoje.strftime("%d/%m/%Y")
            
            logger.info(f"Data início: {data_inicio_str} (90 dias atrás)")
            logger.info(f"Data término: {data_hoje_str} (hoje)")
            
            # Clicar no campo de data início e inserir a data
            logger.info("Clicando no campo de data início...")
            resultado_data_inicio = get_position_img(btn_data_inicio, timeout=6)
            if not resultado_data_inicio:
                raise RuntimeError("Campo de data início não encontrado")
            
            _, coords_data_inicio = resultado_data_inicio
            pyautogui.click(coords_data_inicio)
            time.sleep(0.5)
            
            # Inserir data início usando write_with_retry_formatted
            logger.info(f"Inserindo data início: {data_inicio_str}")
            write_with_retry_formatted(x=coords_data_inicio[0], y=coords_data_inicio[1], expected_text=data_inicio_str, retries=3, delay=0.2)
            
            # Clicar no campo de data término e inserir a data
            logger.info("Clicando no campo de data término...")
            resultado_data_termino = get_position_img(btn_data_termino, timeout=6)
            if not resultado_data_termino:
                raise RuntimeError("Campo de data término não encontrado")
            
            _, coords_data_termino = resultado_data_termino
            pyautogui.click(coords_data_termino)
            time.sleep(0.5)
            
            # Inserir data término usando write_with_retry_formatted
            logger.info(f"Inserindo data término: {data_hoje_str}")
            write_with_retry_formatted(x=coords_data_termino[0], y=coords_data_termino[1], expected_text=data_hoje_str, retries=3, delay=0.2)
            
            # Fazer scroll na página até encontrar a imagem "scroll"
            logger.info("Fazendo scroll na página até encontrar a imagem 'scroll'...")
            sucesso_scroll, tentativas = scroll_until_find_image( target_image=scroll, max_attempts=20, scroll_amount=-500, scroll_delay=1.0, search_timeout=2.0)
            if sucesso_scroll:
                logger.info(f"Scroll concluído com sucesso em {tentativas} tentativas")
            else:
                logger.warning("Imagem 'scroll' não encontrada após todas as tentativas de scroll")
            
            # 1. Clicar em liquidações e verificar sintetico
            logger.info("Clicando em liquidações e verificando sintetico...")
            click_and_verify(btn_liquidacao, btn_sintetico)

            # 2. Clicar em sintetico e verificar pdf
            logger.info("Clicando em sintetico e verificando pdf...")
            click_and_verify(btn_sintetico, btn_pdf)

            # 3. Clicar em pdf e verificar gerar relatório
            logger.info("Clicando em pdf e verificando gerar relatório...")
            click_and_verify(btn_pdf, btn_gerar_relatorio)

            # 4. Clicar em gerar relatório (clique final)
            logger.info("Clicando em gerar relatório...")
            resultado_gerar = get_position_img(btn_gerar_relatorio)
            if not resultado_gerar:
                raise RuntimeError("Botão gerar relatório não encontrado para clique final")
            
            _, coords_gerar = resultado_gerar
            pyautogui.click(coords_gerar)
            time.sleep(1.0)  # Aguardar o relatório ser gerado
            
            logger.info("Sequência de cliques para gerar relatório concluída com sucesso!")
            
            # Aguardar a imagem "impressora" aparecer e clicar nela
            logger.info("Aguardando a imagem 'impressora' aparecer...")
            resultado_impressora = get_position_img(btn_impressora, timeout=30)  # Timeout maior para aguardar geração
            if not resultado_impressora:
                raise RuntimeError("Imagem 'impressora' não apareceu após gerar relatório")
            
            _, coords_impressora = resultado_impressora
            logger.info("Imagem 'impressora' encontrada. Clicando nela...")
            pyautogui.click(coords_impressora)
            time.sleep(1.0)  # Aguardar ação da impressora
            
            # Verificar se a imagem "finalizado" aparece no retângulo especificado
            logger.info("Verificando se 'finalizado' aparece no retângulo especificado...")
            # Usar coordenadas do mapeamento
            regiao_finalizado = COBRANCA_BANCARIA["regiao_finalizado"]["bounds"]
            
            # Procurar por "finalizado" apenas na região especificada
            resultado_finalizado = get_position_img(btn_finalizado, timeout=10, screenshot_region=regiao_finalizado)
            
            if not resultado_finalizado:
                logger.warning("Imagem 'finalizado' não encontrada no retângulo especificado. Encerrando script e retornando None.")
                return None
            else:
                logger.info("Imagem 'finalizado' encontrada no retângulo. Prosseguindo...")
                
                # Clicar nas coordenadas finais usando mapeamento
                logger.info("Clicando nas coordenadas finais...")
                # Usar coordenadas do mapeamento
                left_final, top_final, right_final, bottom_final = COBRANCA_BANCARIA["coordenadas_finais"]["bounds"]
                center_x_final = (left_final + right_final) // 2
                center_y_final = (top_final + bottom_final) // 2
                
                pyautogui.click(center_x_final, center_y_final)
                time.sleep(0.5)
                
                logger.info("Clique nas coordenadas finais executado com sucesso!")
            
                # Aguardar o download do relatório na pasta de downloads
                logger.info("Aguardando download do relatório na pasta de downloads...")
                
                # Configurar timeout para aguardar o download
                timeout_download = 30  # 60 segundos para aguardar o download
                start_time = time.time()
                
                # Caminho da pasta de downloads
                downloads_path = Path.home() / "Downloads"
                
                while time.time() - start_time < timeout_download:
                    # Procurar por arquivos que contêm "Movimento_de_Liquidacoes" no nome
                    movimento_files = [f for f in downloads_path.glob("*.pdf") if "Movimento_de_Liquidacoes" in f.name]
                    if movimento_files:
                        # Pegar o arquivo mais recente
                        latest_file = max(movimento_files, key=lambda f: f.stat().st_mtime)
                        file_age = time.time() - latest_file.stat().st_mtime
                        
                        # Se o arquivo foi criado/modificado nos últimos 10 segundos, é provavelmente o nosso
                        if file_age < 10:
                            # Mover para a pasta temp
                            novo_nome = f"LiquidacoesBaixas_{id_item}_.pdf"
                            relatorio = Path(pasta_destino_final) / novo_nome
                            relatorio.parent.mkdir(parents=True, exist_ok=True)
                            
                            try:
                                import shutil
                                shutil.move(str(latest_file), str(relatorio))
                                logger.success(f"Relatório LiquidacoesBaixas_ movido para: {relatorio}")
                                
                                # Retornar o caminho do relatório baixado
                                return relatorio
                                
                            except Exception as e:
                                logger.error(f"Erro ao mover arquivo: {e}")
                                raise
                    
                    time.sleep(1)
                else:
                    logger.warning("Timeout aguardando download do relatório Movimento_de_Liquidacoes")
                    return None
    except Exception as e:
        logger.error(f"Erro ao baixar relatórios do PAINEL COMERCIAL: {e}")
        # Fechar o Chrome mesmo em caso de erro
        try:
            error_handler(win_modulo)
        except Exception as eh:
            logger.warning(f"Falha ao executar error_handler: {eh}")
            logger.info("Fechando o Chrome devido a erro...")
            fechar_leitor_pdf()
            raise

class DummyWin:
    def set_focus(self):
        pass

if __name__ == "__main__":
    win_modulo = DummyWin()
    id_item = "123"
    PASTA_RELATORIOS_FINAL = str(project_root / "temp/relatorios_finais")
    logger.info("Iniciando teste de download do relatório Conta Corrente...")
    associado_desde = "29/04/2025"
    cpf_cnpj = "37598843000141"
    dicionario_caminhos_prints = baixar_relatorio_conta_corrente(win_modulo, id_item, PASTA_RELATORIOS_FINAL, associado_desde, cpf_cnpj)
    logger.info(f"Caminhos dos prints salvos: {dicionario_caminhos_prints}")
