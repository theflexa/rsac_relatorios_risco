import pyautogui
import cv2
import numpy as np
import time
import psutil
from pathlib import Path
from loguru import logger
# C:\Automations\lib_sisbr_desktop\tests\plataforma_atendimento_acesso_cpfcnpj.py
import time
import os
import shutil
import psutil
import pyautogui
import cv2
import numpy as np
import sys
from pathlib import Path
# Adiciona o diretório raiz do projeto ao sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from loguru import logger
from pywinauto.keyboard import send_keys
from pywinauto.timings import TimeoutError
from pathlib import Path
from src.lib_sisbr_desktop.utils.utils import encontrar_relatorios_na_tela, logar_relatorios_encontrados, fechar_janela_ged
from src.lib_sisbr_desktop.gui.helpers import click_coords_and_verify
from src.lib_sisbr_desktop.gui.mapeamento import ROI_RELATORIO
 #Caminho dos templates
current_file = Path(__file__).resolve()
# parent.parent = .../lib_sisbr_desktop
lib_project_root = current_file.parent.parent  # Ajuste o número de "parent"
ocr_path = (lib_project_root / "src" / "lib_sisbr_desktop" / "ocr" / "plataforma_de_atendimento").resolve()
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, os.path.abspath(os.path.join(project_root, '../bot_agent/src')))

def mover_relatorio_baixado(pasta_origem_str: str, pasta_destino_str: str, id_item: str) -> str:
    pasta_origem = Path(pasta_origem_str)
    pasta_destino = Path(pasta_destino_str)
    pasta_destino.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Aguardando download de PDF na pasta: {pasta_origem}")
    timeout = 90
    end_time = time.time() + timeout
    arquivo_encontrado = None

    while time.time() < end_time:
        arquivos_pdf = list(pasta_origem.glob("*.pdf"))
        if arquivos_pdf:
            arquivo_encontrado = max(arquivos_pdf, key=os.path.getctime)
            logger.success(f"PDF baixado detectado: {arquivo_encontrado.name}")
            break
        time.sleep(1)

    if not arquivo_encontrado:
        raise TimeoutError("Timeout: Nenhum arquivo PDF foi encontrado na pasta de downloads.")

    time.sleep(5)
    fechar_leitor_pdf()
    time.sleep(1)

    #nome_final = f"SERASA_{id_item}.pdf"
    caminho_final = pasta_destino / arquivo_encontrado.name
    
    logger.info(f"Movendo '{arquivo_encontrado.name}' para '{caminho_final}'...")
    shutil.move(str(arquivo_encontrado), str(caminho_final))
    
    return str(caminho_final)

def fechar_leitor_pdf(process_name="msedge.exe"):
    logger.info(f"Verificando e encerrando processos de '{process_name}'...")
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'].lower() == process_name.lower():
            try:
                p = psutil.Process(proc.info['pid'])
                p.kill()
                logger.warning(f"Processo '{process_name}' (PID: {proc.info['pid']}) foi encerrado.")
            except Exception as e:
                logger.error(f"Erro ao encerrar processo de PDF: {e}")

def esperar_edge_abrir(timeout=30):
    import psutil
    import time
    logger.info("Aguardando o Edge abrir para fechar...")
    start = time.time()
    while time.time() - start < timeout:
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] and proc.info['name'].lower() == "msedge.exe":
                logger.info("Edge detectado!")
                return True
        time.sleep(0.5)
    logger.warning("Edge não foi detectado dentro do tempo limite.")
    return False

def baixar_relatorio_faturamento_renda(win_modulo, id_item: str, pasta_destino_final: str, cpf_cnpj, cooperativa: str):
    """
    Executa o fluxo completo de download do relatório de Faturamento/Renda.
    """
    logger.info("Iniciando processo de download do relatório de Faturamento/Renda.")
    win_modulo.set_focus()
    
    # Mapeamento
    template_relatorio_renda = ocr_path / "Rendas/search.png"
    template_relatorio_relatorio = ocr_path / "Rendas/comprovante.png"
    template_verificacao = ocr_path / "Rendas/verificacao.png"

    template_renda = cv2.imread(str(template_relatorio_renda), cv2.IMREAD_COLOR)
    h_renda, w_renda, _ = template_renda.shape
    template_relatorio = cv2.imread(str(template_relatorio_relatorio), cv2.IMREAD_COLOR)
    h_rel, w_rel, _ = template_relatorio.shape

    pontos_relatorio_renda = encontrar_relatorios_na_tela(template_relatorio_renda)

    logar_relatorios_encontrados(pontos_relatorio_renda)

    caminhos_baixados = []
    relatorios_por_renda = []

    if not pontos_relatorio_renda:
        logger.info("Nenhuma renda encontrada na tela.")
        return
    for idx_renda, (x_renda, y_renda) in enumerate(pontos_relatorio_renda):
        caminhos_renda = []
        logger.info(f"Clicando na lupa de renda {idx_renda+1} em (x={x_renda}, y={y_renda})")
        # Clicar na lupa da renda e aguardar o objeto de verificação
        
        click_coords_and_verify((x_renda + w_renda // 2, y_renda + h_renda // 2), str(template_verificacao))
        time.sleep(0.5)
        # Buscar todas as lupas de relatório (comprovante.png) na nova tela, apenas na região do relatório
        timeout_relatorio = 30  # segundos
        start_time_relatorio = time.time()
        pontos_relatorio_relatorio = []
        while not pontos_relatorio_relatorio and (time.time() - start_time_relatorio < timeout_relatorio):
            pontos_relatorio_relatorio = encontrar_relatorios_na_tela(template_relatorio_relatorio, roi=ROI_RELATORIO)
            if not pontos_relatorio_relatorio:
                time.sleep(1)
        if not pontos_relatorio_relatorio:
            logger.warning("Nenhum relatório encontrado após clicar na renda. Reinicie o SISBR.")
        logar_relatorios_encontrados(pontos_relatorio_relatorio)
        for idx_rel, (x_rel, y_rel) in enumerate(pontos_relatorio_relatorio):
            logger.info(f"Clicando na lupa de relatório {idx_rel+1} da renda {idx_renda+1} em (x={x_rel}, y={y_rel})")
            pyautogui.click(x_rel + w_rel // 2, y_rel + h_rel // 2)
            pasta_download_temp = os.path.join(
                os.environ['USERPROFILE'],
                'AppData', 'Roaming', 'br.com.sicoob.sisbr.portalAir', 'Local Store', f'{cooperativa}'
            )
            caminho_pdf = mover_relatorio_baixado(pasta_download_temp, pasta_destino_final, id_item)
            caminhos_renda.append(caminho_pdf)
            fechar_janela_ged()
        relatorios_por_renda.append(caminhos_renda)
        logger.info("Voltando para a tela de rendas...")
        pyautogui.press('esc')
        time.sleep(1)

    # Passo 7: Gerenciar o download do arquivo PDF
    logger.info("Gerenciando o download do arquivo PDF...")
    caminhos_baixados_dict = {}
    for idx_renda, caminhos_renda in enumerate(relatorios_por_renda):
        for idx_rel, caminho_final_relatorio in enumerate(caminhos_renda):
            nome_final = f"ComprovanteRendas_{idx_renda}_{idx_rel}_{id_item}_{cpf_cnpj}.pdf"
            novo_caminho = os.path.join(os.path.dirname(caminho_final_relatorio), nome_final)
            os.rename(caminho_final_relatorio, novo_caminho)
            logger.info(f"Relatório renomeado para: {novo_caminho}")
            caminhos_baixados_dict[(idx_renda, idx_rel)] = novo_caminho
    logger.success("Relatórios Faturamento/Renda salvos com sucesso.")
    return caminhos_baixados_dict

if __name__ == "__main__":
    # Mock de parâmetros para teste
    class DummyWin:
        def set_focus(self):
            pass
    win_modulo = DummyWin()
    id_item = "123"
    PASTA_RELATORIOS_FINAL = str(project_root / "temp/relatorios_finais")
    cpf_cnpj = "00000000000"
    cooperativa = "3059"
    baixar_relatorio_faturamento_renda(win_modulo, id_item, PASTA_RELATORIOS_FINAL, cpf_cnpj, cooperativa)