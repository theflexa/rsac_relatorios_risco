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

# Caminho dos templates
current_file = Path(__file__).resolve()
lib_project_root = current_file.parent.parent
ocr_path = (lib_project_root / "src" / "lib_sisbr_desktop" / "ocr" / "plataforma_de_atendimento").resolve()
ocr_lancamentos = (lib_project_root / "src" / "lib_sisbr_desktop" / "ocr" / "conta_corrente").resolve()


@retry(times=3, delay_s=2)
def baixar_relatorio_lancamentos(win_modulo, id_item: str, pasta_destino_final: str, cpf_cnpj):
    """
    Baixa o relatório de lançamentos do módulo CONTA CORRENTE.
    """
    logger.info("Iniciando download do relatório de LANÇAMENTOS...")
    win_modulo.set_focus()
    
    try:
        # Passo 1 - Clicar em "Relatório"
        logger.info("Clicando em 'Relatório'...")
        btn_relatorio = ocr_lancamentos / "relatorio.png"
        btn_relatorio_lancamentos = ocr_lancamentos / "relatorio_de_lancamentos.png"
        click_and_verify(btn_relatorio, btn_relatorio_lancamentos)
        
        # Passo 2 - Clicar em "Relatório de Lançamentos"
        logger.info("Clicando em 'Relatório de Lançamentos'...")
        btn_lancamentos = ocr_lancamentos / "lancamentos.png"
        click_and_verify(btn_relatorio_lancamentos, btn_lancamentos)
        
        # Passo 3 - Clicar em "Lançamentos"
        logger.info("Clicando em 'Lançamentos'...")
        btn_lancamentos_conta = ocr_lancamentos / "lancamentos_conta.png"
        click_and_verify(btn_lancamentos, btn_lancamentos_conta)
        
        # Passo 4 - Clicar em "Lançamentos Conta"
        logger.info("Clicando em 'Lançamentos Conta'...")
        # Como não há uma imagem específica para verificar após o clique, usamos um tempo de espera
        # ou podemos usar a mesma imagem como verificação temporária
        click_and_verify(btn_lancamentos_conta, btn_lancamentos_conta, verify_threshold=0.8)
        time.sleep(2)
        
        # Passo 5 - Inserir número da conta inicial
        logger.info("Inserindo número da conta inicial...")
        coord_conta_inicial = {'l': 703, 't': 355, 'w': 91, 'h': 17}
        
        # Clicar no centro do campo conta inicial
        x_centro_inicial = coord_conta_inicial['l'] + coord_conta_inicial['w'] // 2
        y_centro_inicial = coord_conta_inicial['t'] + coord_conta_inicial['h'] // 2
        pyautogui.click(x_centro_inicial, y_centro_inicial)
        time.sleep(0.5)
        write_with_retry_formatted(x_centro_inicial, y_centro_inicial, "30.513-8")  # Substitua pelo número da conta real
        logger.success("Número da conta inicial inserido e validado")
        time.sleep(1)
        
        # Passo 6 - Inserir número da conta final
        logger.info("Inserindo número da conta final...")
        # Usar a mesma coordenada base da conta inicial, mas ajustar para baixo
        coord_conta_final = {'l': 703, 't': 382, 'w': 91, 'h': 17}  # 30 pixels abaixo da conta inicial
        
        # Clicar no centro do campo conta final
        x_centro_final = coord_conta_final['l'] + coord_conta_final['w'] // 2
        y_centro_final = coord_conta_final['t'] + coord_conta_final['h'] // 2
        pyautogui.click(x_centro_final, y_centro_final)
        time.sleep(0.5)
        write_with_retry_formatted(x_centro_final, y_centro_final, "30.513-8")  # Substitua pelo número da conta real
        logger.success("Número da conta final inserido e validado")
        time.sleep(1)
        
        # Passo 7 - Inserir data inicial (hoje - 90 dias)
        logger.info("Inserindo data inicial (hoje - 90 dias)...")
        from datetime import datetime, timedelta
        data_inicial = (datetime.now() - timedelta(days=90)).strftime("%d/%m/%Y")
        coord_data_inicial = {'l': 923, 't': 356, 'w': 86, 'h': 17}
        
        # Clicar no centro do campo data inicial
        x_centro_data_inicial = coord_data_inicial['l'] + coord_data_inicial['w'] // 2
        y_centro_data_inicial = coord_data_inicial['t'] + coord_data_inicial['h'] // 2
        pyautogui.click(x_centro_data_inicial, y_centro_data_inicial)
        time.sleep(0.5)
        write_with_retry_formatted(x_centro_data_inicial, y_centro_data_inicial, data_inicial)
        logger.success(f"Data inicial inserida e validada: {data_inicial}")
        time.sleep(1)
        
        # Passo 8 - Inserir data final (hoje)
        logger.info("Inserindo data final (hoje)...")
        data_final = datetime.now().strftime("%d/%m/%Y")
        coord_data_final = {'l': 923, 't': 382, 'w': 86, 'h': 17}
        
        # Clicar no centro do campo data final
        x_centro_data_final = coord_data_final['l'] + coord_data_final['w'] // 2
        y_centro_data_final = coord_data_final['t'] + coord_data_final['h'] // 2
        pyautogui.click(x_centro_data_final, y_centro_data_final)
        time.sleep(0.5)
        write_with_retry_formatted(x_centro_data_final, y_centro_data_final, data_final)
        logger.success(f"Data final inserida e validada: {data_final}")
        time.sleep(1)
        
        # Passo 9 - Inserir códigos em loop
        logger.info("Inserindo códigos em loop...")
        codigos = ["510", "511", "512", "550", "820", "821", "822", "829", "830", "7286", "7529", "7043", "7301", "7302", "7368", "7370"]
        coord_codigo = {'l': 663, 't': 564, 'w': 61, 'h': 17}
        btn_adicionar = ocr_lancamentos / "adicionar.png"
        
        for i, codigo in enumerate(codigos, 1):
            logger.info(f"Inserindo código {i}/{len(codigos)}: {codigo}")
            
            # Clicar no centro do campo código
            x_centro_codigo = coord_codigo['l'] + coord_codigo['w'] // 2
            y_centro_codigo = coord_codigo['t'] + coord_codigo['h'] // 2
            pyautogui.click(x_centro_codigo, y_centro_codigo)
            time.sleep(0.5)
            
            # Inserir o código
            write_with_retry_formatted(x_centro_codigo, y_centro_codigo, codigo)
            time.sleep(0.5)
            
            # Navegar e confirmar com Tab + Tab + Enter
            pyautogui.press('tab')
            time.sleep(0.2)
            pyautogui.press('tab')
            time.sleep(0.2)
            pyautogui.press('enter')
            time.sleep(1)
            
            logger.success(f"Código {codigo} inserido e adicionado com sucesso")
        
        logger.success(f"Todos os {len(codigos)} códigos foram inseridos com sucesso")
        
        # Passo 10 - Clicar no botão OK
        logger.info("Clicando no botão OK...")
        btn_ok = ocr_lancamentos / "ok.png"
        btn_imprimir = ocr_lancamentos / "imprimir.png"
        click_and_verify(btn_ok, btn_imprimir)
        
        # Passo 11 - Clicar no botão Imprimir
        logger.info("Clicando no botão Imprimir...")
        # Encontrar e clicar no botão imprimir
        result_imprimir = get_position_img(btn_imprimir, threshold=0.87, timeout=30)
        if not result_imprimir:
            raise RuntimeError("Botão imprimir não encontrado")
        
        _, (x_imprimir, y_imprimir) = result_imprimir
        logger.info(f"Botão imprimir encontrado em ({x_imprimir}, {y_imprimir})")
        pyautogui.click(x_imprimir, y_imprimir)
        # Aguardar um pouco para o download iniciar
        time.sleep(3)
        
        # Passo 12 - Gerenciar o download do arquivo PDF
        logger.info("Gerenciando o download do arquivo PDF...")
        pasta_download_temp = os.path.join(os.environ['USERPROFILE'], 'temp', 'relAssinc')
        
        # Importar e usar a função mover_relatorio_baixado do padrão Serasa/Bacen
        from tests.plataforma_atendimento import mover_relatorio_baixado
        caminho_final_relatorio = mover_relatorio_baixado(pasta_download_temp, pasta_destino_final, id_item)
        
        # Renomear o arquivo conforme o padrão
        nome_final = f"Lancamentos_{id_item}_{cpf_cnpj}.pdf"
        novo_caminho = os.path.join(os.path.dirname(caminho_final_relatorio), nome_final)
        if os.path.exists(novo_caminho):
            os.remove(novo_caminho)
        os.rename(caminho_final_relatorio, novo_caminho)

        logger.success(f"Relatório de LANÇAMENTOS salvo com sucesso em: {novo_caminho}")
        return novo_caminho
        
    except Exception as e:
        logger.error(f"Erro ao baixar relatório de LANÇAMENTOS: {e}")
        raise


class DummyWin:
    def set_focus(self):
        pass


if __name__ == "__main__":
    win_modulo = DummyWin()
    id_item = "123"
    cpf_cnpj = "70852015178"  # CPF de teste
    PASTA_RELATORIOS_FINAL = str(project_root / "temp/relatorios_finais")
    
    logger.info("Iniciando teste de download do relatório de LANÇAMENTOS...")
    caminho_relatorio = baixar_relatorio_lancamentos(win_modulo, id_item, PASTA_RELATORIOS_FINAL, cpf_cnpj)
    logger.info(f"Caminho do relatório salvo: {caminho_relatorio}")