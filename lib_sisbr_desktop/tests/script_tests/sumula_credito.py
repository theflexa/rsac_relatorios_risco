import sys
import time
from pathlib import Path
from loguru import logger

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import pyautogui
from PIL import Image, ImageChops, ImageStat
import pytesseract
import os
from src.lib_sisbr_desktop.gui.helpers import get_position_img, click_and_verify, verificar_campo_muda_de_cor
from src.lib_sisbr_desktop.utils.retry import retry
from src.lib_sisbr_desktop.gui.typer import write_with_retry_formatted
from tests.plataforma_atendimento import acessa_submodulo

# Caminho dos templates
current_file = Path(__file__).resolve()
lib_project_root = current_file.parent.parent


@retry(times=3, delay_s=2)
def baixar_sumula_credito(win_modulo, id_item: str, pasta_destino_final: str, numero_proposta="123456"):
    """
    Baixa a súmula de crédito do módulo de CRÉDITO usando o número da proposta.
    """
    logger.info("Iniciando download da SÚMULA DE CRÉDITO...")
    win_modulo.set_focus()

    ocr_credito = (lib_project_root / "src" / "lib_sisbr_desktop" / "ocr" / "plataforma_de_credito").resolve()

    try:
        # Passo 1 - Acessar o módulo de Crédito
        logger.info("Acessando o módulo de Crédito...")
        # Clicar em Operações de Crédito
        btn_operacoes_credito = ocr_credito / "operacoes_credito.png"
        btn_mesa_operacoes = ocr_credito / "mesa_operacoes.png"
        btn_verify = ocr_credito / "menu_mesa_de_operacoes.png"

        logger.info("Clicando em 'Operações de Crédito'...")
        click_and_verify(btn_operacoes_credito, btn_mesa_operacoes)
        
        # Passo 2 - Clicar em Mesa de Operações
        logger.info("Clicando em 'Mesa de Operações'...")
        time.sleep(1)  # Aguardar antes de clicar
        click_and_verify(btn_mesa_operacoes, btn_verify)
        time.sleep(1.5)  # Aguardar após clicar para garantir carregamento
              
        # Passo 3 - Inserir número da proposta
        logger.info("Inserindo número da proposta...")
        
        # Inserir número da proposta usando coordenadas fixas
        coord_x_proposta, coord_y_proposta = 627, 292  # Centro do BoundingRectangle {l:563 t:284 r:692 b:301}
        logger.info(f"Inserindo número da proposta nas coordenadas ({coord_x_proposta}, {coord_y_proposta})")
        write_with_retry_formatted(coord_x_proposta, coord_y_proposta, numero_proposta)  # Número da proposta
        logger.success(f"Número da proposta {numero_proposta} inserido e validado")
        time.sleep(1)
        
        # Passo 4 - Pressionar Enter para buscar
        logger.info("Pressionando Enter para buscar...")
        pyautogui.press('enter')
        time.sleep(5)  # Aumentado o tempo de espera para carregamento dos resultados
        
        # Passo 5 - Verificar se há resultados
        logger.info("Verificando resultados...")
        # Aqui você pode adicionar uma verificação para confirmar que os resultados foram carregados
        # Por exemplo, procurar por uma imagem que indique que há resultados
        
        # Passo 6 - Clicar na proposta (coordenadas específicas)
        logger.info("Clicando na proposta nas coordenadas especificadas...")
        # Coordenadas do retângulo {l:805, t:479, r:1074, b:493}
        left, top, right, bottom = 805, 479, 1074, 493
        # Calcular o centro do retângulo
        center_x = (left + right) // 2
        center_y = (top + bottom) // 2
        logger.info(f"Clicando no centro da proposta em ({center_x}, {center_y})")
        time.sleep(1.5)  # Aguardar antes de clicar
        pyautogui.click(center_x, center_y)
        time.sleep(2)  # Aumentado o tempo de espera após clicar
        
        # Passo 7 - Clicar no botão Abrir
        logger.info("Clicando no botão 'Abrir'...")
        btn_abrir = ocr_credito / "abrir.png"
        btn_pareceres = ocr_credito / "pareceres.png"
        logger.info("Clicando em 'Abrir'...")
        time.sleep(1)  # Aguardar antes de clicar
        click_and_verify(btn_abrir, btn_pareceres)
        time.sleep(1.5)  # Aguardar após clicar
        
        # Passo 8 - Clicar no botão Pareceres
        logger.info("Clicando no botão 'Pareceres'...")
        btn_imprimir = ocr_credito / "imprimir.png"
        logger.info("Clicando em 'Pareceres'...")
        time.sleep(1)  # Aguardar antes de clicar
        click_and_verify(btn_pareceres, btn_imprimir)
        time.sleep(2)  # Aguardar após clicar
        
        # Passo 9 - Clicar no botão Imprimir pela primeira vez
        logger.info("Clicando no botão 'Imprimir' pela primeira vez...")
        logger.info("Clicando em 'Imprimir'...")
        time.sleep(1.5)  # Aguardar antes de clicar
        # Usamos o mesmo botão como verificação, com um threshold menor
        click_and_verify(btn_imprimir, btn_imprimir, verify_threshold=0.8)
        time.sleep(2)  # Aguardar após clicar
        
        # Passo 10 - Aguardar a imagem do PDF aparecer
        logger.info("Aguardando a imagem do PDF aparecer...")
        img_pdf = ocr_credito / "pdf.png"
        result_pdf = get_position_img(img_pdf, threshold=0.8, timeout=30)
        if not result_pdf:
            logger.warning("Imagem do PDF não encontrada, mas continuando...")
        else:
            logger.success("Imagem do PDF encontrada!")
            # Passo 11 - Clicar no botão Imprimir novamente
            logger.info("Clicando no botão 'Imprimir' novamente...")
            result_imprimir = get_position_img(btn_imprimir, threshold=0.8, timeout=10)
            time.sleep(2)  # Aguardar antes de verificar o botão imprimir
            if result_imprimir:
                _, (x_imprimir, y_imprimir) = result_imprimir
                logger.info(f"Botão imprimir encontrado em ({x_imprimir}, {y_imprimir})")
                time.sleep(1)  # Aguardar antes de clicar
                pyautogui.click(x_imprimir, y_imprimir)
                logger.success("Clicado em 'Imprimir' pela segunda vez!")
                time.sleep(3)  # Aguardar após clicar para processamento
            else:
                logger.warning("Botão imprimir não encontrado para o segundo clique")
        
        # Passo 12 - Aguardar o download do PDF
        logger.info("Aguardando o download do PDF...")
        # Aumentar o tempo de espera para garantir que o download inicie
        time.sleep(5)
        
        # Passo 13 - Gerenciar o download do arquivo PDF
        logger.info("Gerenciando o download do arquivo PDF...")
        pasta_download_temp = os.path.join(os.environ['USERPROFILE'], 'temp', 'relAssinc')
        
        # Importar e usar a função mover_relatorio_baixado do padrão Serasa/Bacen
        from tests.plataforma_atendimento import mover_relatorio_baixado
        caminho_final_relatorio = mover_relatorio_baixado(pasta_download_temp, pasta_destino_final, id_item)
        
        # Renomear o arquivo conforme o padrão
        nome_final = f"SumulaCredito_{id_item}_Proposta{numero_proposta}.pdf"
        novo_caminho = os.path.join(os.path.dirname(caminho_final_relatorio), nome_final)
        if os.path.exists(novo_caminho):
            os.remove(novo_caminho)
        os.rename(caminho_final_relatorio, novo_caminho)

        logger.success(f"SÚMULA DE CRÉDITO salva com sucesso em: {novo_caminho}")
        return novo_caminho
        
    except Exception as e:
        logger.error(f"Erro ao baixar SÚMULA DE CRÉDITO: {e}")
        raise

class DummyWin:
    def set_focus(self):
        pass


def teste_isolado_sumula_credito():
    # Importações necessárias para o teste isolado
    from src.lib_sisbr_desktop.core.abrir_sisbr import abrir_sisbr
    from src.lib_sisbr_desktop.core.login import login
    from src.lib_sisbr_desktop.core.acessar_modulo import acessar_modulo
    from src.lib_sisbr_desktop.utils.status import is_logado
    from src.lib_sisbr_desktop.utils.error_handler import error_handler
    import traceback
    import argparse
    from dotenv import load_dotenv
    import psutil
    
    # Configurações do teste
    id_item = "123"
    numero_proposta = "257225720108"  # Número da proposta para teste
    PASTA_RELATORIOS_FINAL = str(project_root / "temp/relatorios_finais")
    NOME_MODULO = "PLATAFORMA DE CRÉDITO"
    
    try:
        # ================================================
        # INIT APPLICATIONS
        # ================================================
        logger.info("Abrindo e fazendo login no Sisbr...")
        app, win_principal = abrir_sisbr()
        if not is_logado(win_principal):
            if not login(): raise RuntimeError("Falha no login.")
        
        # ================================================
        # DOWNLOAD SÚMULA DE CRÉDITO
        # ================================================
        logger.info(f"Acessando o módulo '{NOME_MODULO}'...")
        win_credito = acessar_modulo(win_principal, NOME_MODULO, 5)
        if not win_credito:
            raise RuntimeError(f"Falha ao obter a janela do módulo '{NOME_MODULO}'.")
        time.sleep(3)
        
        logger.info(f"Acessando submódulo 'EMPRÉSTIMO'...")
        acessa_submodulo(win_credito, "EMPRÉSTIMO", plataforma="PLATAFORMA DE CRÉDITO")

        logger.info("Baixando SÚMULA DE CRÉDITO...")
        caminho_sumula = baixar_sumula_credito(win_credito, id_item, PASTA_RELATORIOS_FINAL, numero_proposta)
        logger.info(f"SÚMULA DE CRÉDITO salva em: {caminho_sumula}")
        
        logger.success("--- TESTE DA SÚMULA DE CRÉDITO CONCLUÍDO COM SUCESSO ---")
        return caminho_sumula
        
    except Exception as e:
        logger.error(f"Ocorreu um erro durante o teste: {e}")
        logger.error(traceback.format_exc())
        screenshot_path = project_root / f"logs/error_screenshot_sumula_credito_{id_item}.png"
        pyautogui.screenshot(str(screenshot_path))
        logger.error(f"Screenshot do erro salvo em: {screenshot_path}")
        logger.critical("--- TESTE DA SÚMULA DE CRÉDITO FALHOU ---")
        if 'win_credito' in locals():
            error_handler(win_credito)
        raise

def fechar_todas_instancias_sisbr():
    for proc in psutil.process_iter(['pid', 'name']):
        if 'sisbr' in proc.info['name'].lower():
            try:
                proc.kill()
                logger.info(f"Processo Sisbr (PID: {proc.info['pid']}) encerrado.")
            except Exception as e:
                logger.warning(f"Erro ao encerrar processo Sisbr: {e}")

def main_loop():
    while True:
        try:
            teste_isolado_sumula_credito()
            break  # Sai do loop se rodar com sucesso
        except Exception as e:
            logger.critical(f"Erro fatal detectado: {e}")
            fechar_todas_instancias_sisbr()
            logger.info("Aguardando 10 segundos antes de reiniciar o processo...")
            time.sleep(10)
            logger.info("Reiniciando o processo do zero...")

if __name__ == "__main__":
    # Configuração básica para teste isolado
    import psutil
    
    logger.info("Iniciando teste isolado de download da SÚMULA DE CRÉDITO...")
    main_loop()
    logger.info("Teste isolado finalizado.")