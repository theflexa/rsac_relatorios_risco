# C:\Automations\lib_sisbr_desktop\tests\plataforma_atendimento_acesso_cpfcnpj.py
import time
import os
import shutil
import psutil
import pyautogui
import cv2
import numpy as np
from datetime import datetime, timedelta

from loguru import logger
from pywinauto.keyboard import send_keys
from pywinauto.timings import TimeoutError
from pathlib import Path
from src.lib_sisbr_desktop.utils.wait import wait_for_element
from src.lib_sisbr_desktop.utils.retry import retry
from src.lib_sisbr_desktop.gui.mapeamento import PLATAFORMA_DE_ATENDIMENTO, PLATAFORMA_DE_CREDITO, COBRANCA_BANCARIA, PLATAFORMA_DE_CREDENCIAMENTO
from src.lib_sisbr_desktop.gui.typer import type_with_retry, write_with_retry, write_with_retry_formatted, write_without_verify
from src.lib_sisbr_desktop.gui.helpers import find_edit_by_rect, get_position_img, find_first_template_match, click_and_verify, click_coords_and_verify_double, scroll_until_find_image, verificar_mudanca_cor_dinamica, buscar_com_scroll, get_position_img_ordered
from src.lib_sisbr_desktop.utils.utils import encontrar_relatorios_na_tela, logar_relatorios_encontrados, fechar_janela_ged
from src.lib_sisbr_desktop.gui.mapeamento import ROI_RELATORIO
from src.lib_sisbr_desktop.gui.helpers import click_coords_and_verify
from src.lib_sisbr_desktop.gui.mapeamento import RETANGULOS_CONTACORRENTE_RECT, REGIAO_PRINT
from src.lib_sisbr_desktop.utils.screen_utils import  salvar_print_regiao
from src.lib_sisbr_desktop.utils.error_handler import error_handler
from src.lib_sisbr_desktop.gui.helpers import verificar_campo_muda_de_cor, double_click_coords, get_position_img
from src.lib_sisbr_desktop.gui.helpers import get_position_img
from src.lib_sisbr_desktop.utils.window import fechar_modulo
from src.lib_sisbr_desktop.core.acessar_modulo import acessar_modulo
# Caminho dos templates
current_file = Path(__file__).resolve()
# parent.parent = .../lib_sisbr_desktop
lib_project_root = current_file.parent.parent  # Ajuste o número de "parent"
ocr_path = (lib_project_root / "src" / "lib_sisbr_desktop" / "ocr" / "plataforma_de_atendimento").resolve()
ocr_credito = (lib_project_root / "src" / "lib_sisbr_desktop" / "ocr" / "plataforma_de_credito").resolve()
def fechar_popup_ia():
    """
    Fecha o pop-up da IA que aparece quando a plataforma de atendimento é aberta.
    Clica diretamente nas coordenadas fornecidas.
    """
    logger.info("Verificando e fechando pop-up da IA...")
    
    try:
        time.sleep(3)
        # Clica no centro do pop-up da IA
        x_centro_popup, y_centro_popup = 1839, 962
        logger.info(f"Clicando no centro do pop-up da IA em ({x_centro_popup}, {y_centro_popup})")
        pyautogui.moveTo(x_centro_popup, y_centro_popup)
        time.sleep(3)

        # Clica no centro do botão de fechar
        x_centro_fechar, y_centro_fechar = 1863, 841
        logger.info(f"Clicando no botão de fechar em ({x_centro_fechar}, {y_centro_fechar})")
        pyautogui.moveTo(x_centro_fechar, y_centro_fechar)
        pyautogui.click()
        
        logger.success("Pop-up da IA fechado com sucesso")
        
        time.sleep(1)
    except Exception as e:
        logger.info("Erro ao fechar pop-up da IA - pode não estar presente")

@retry(times=3, delay_s=2)
def acessar_cliente_por_cpf_cnpj(win_modulo, cpf_cnpj: str):
    win_modulo.set_focus()
    logger.info(f"CPF/CNPJ: {cpf_cnpj}")
    
    templates = [
        ocr_path / "cpfcnpj.png",
        ocr_path / "cliente_pesquisado.png",
    ]
    result = find_first_template_match(templates, threshold=0.87, timeout=20)

    if result:
        template_found, pos = result
        logger.info(f"Match encontrado na imagem: {template_found} {pos}")

        if str(template_found).endswith("cpfcnpj.png"):
            # Digita CPF/CNPJ
            x, y = pos
            write_with_retry(x, y, cpf_cnpj)
            
        elif str(template_found).endswith("cliente_pesquisado.png"):
            # Busca e clica no botão de ação (ou outro campo)
            botao_acao_img = ocr_path / "search.png"
            _, pos = get_position_img(botao_acao_img, threshold=0.87, timeout=5)
            if pos:
                logger.info(f"Botão de ação encontrado em: {pos}")
                pyautogui.click(pos)
                _, pos = get_position_img(ocr_path / "cpfcnpj.png", threshold=0.90, timeout=7)
                x, y = pos
                write_with_retry(x, y, cpf_cnpj)                
            else:
                logger.warning("Botão de ação não encontrado após cliente pesquisado.")
            # Lançar EXCEPTION ?

        else:
            logger.warning(f"Template inesperado encontrado: {template_found}")

    else:
        logger.warning("Nenhuma imagem de campo ou cliente encontrada. Abortando rotina.")
        try:
            error_handler(win_modulo)
        except Exception as e:
            logger.warning(f"Falha ao executar error_handler: {e}")
        raise RuntimeError("Template não encontrado, tentando novamente...")
    
    logger.info("Pressionando ENTER para buscar o cliente...")
    send_keys('{ENTER}')
    time.sleep(3)
    logger.success(f"Cliente com documento '{cpf_cnpj}' buscado. Tela pronta para a próxima etapa.")

@retry(times=3, delay_s=2)
def acessa_submodulo(win_modulo, submodulo: str, plataforma: str = "ATENDIMENTO"):
    logger.info("Navegando para o submódulo " + submodulo + " ...")
    # Definir os bounds de acordo com a plataforma
    if plataforma == "PLATAFORMA DE CRÉDITO":
        logger.info("Executando lógica específica para Plataforma de Crédito...")
        # Fazer hover na imagem menu_plataforma_de_credito
        try:
            btn_menu_credito = ocr_credito / "menu_plataforma_de_credito.png"
            menu_position = get_position_img(btn_menu_credito)
            
            if menu_position:
                logger.info(f"Fazendo hover na imagem menu_plataforma_de_credito na posição: {menu_position}")
                for _ in range(5):
                    pyautogui.press('esc')
                    time.sleep(0.5)
                pyautogui.moveTo(menu_position[0], menu_position[1])
                time.sleep(1)
                
                bounds = PLATAFORMA_DE_CREDITO["edit_search_submodulo"]["bounds"]
                logger.info(f"Procurando e clicando no retângulo com bounds: {bounds} (tolerância aumentada)")
                # Aqui, vamos clicar diretamente nas coordenadas do centro do bounds e digitar o texto usando write_with_retry
                x = (bounds[0] + bounds[2]) // 2
                y = (bounds[1] + bounds[3]) // 2
                write_with_retry(x, y, submodulo)               
                time.sleep(3)
                send_keys('{DOWN}{ENTER}')
            else:
                logger.error("Imagem menu_plataforma_de_credito não encontrada")
                raise RuntimeError("Template menu_plataforma_de_credito não encontrado")
        except Exception as e:
            logger.error(f"Erro ao executar lógica da Plataforma de Crédito: {e}")
            raise
    elif plataforma == "PLATAFORMA DE ATENDIMENTO":
        bounds = PLATAFORMA_DE_ATENDIMENTO["edit_search_submodulo"]["bounds"]
        campo_busca_submodulo = find_edit_by_rect(win_modulo, bounds)
    
        # Comportamento comum para ambas as plataformas
        type_with_retry(campo_busca_submodulo, submodulo, wait=2.5)
        time.sleep(3)
        send_keys('{DOWN}{ENTER}')

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

def fechar_chrome(process_name="chrome.exe"):
    logger.info(f"Verificando e encerrando processos do '{process_name}'...")
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'].lower() == process_name.lower():
            try:
                p = psutil.Process(proc.info['pid'])
                p.kill()
                logger.warning(f"Processo '{process_name}' (PID: {proc.info['pid']}) foi encerrado.")
            except Exception as e:
                logger.error(f"Erro ao encerrar processo do Chrome: {e}")

def mover_relatorio_baixado(pasta_origem_str: str, pasta_destino_str: str, id_item: str) -> str:
    pasta_origem = Path(pasta_origem_str)
    pasta_destino = Path(pasta_destino_str)
    pasta_destino.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Aguardando download de PDF na pasta: {pasta_origem} e subpastas")
    timeout = 90
    end_time = time.time() + timeout
    arquivo_encontrado = None

    while time.time() < end_time:
        arquivos_pdf = list(pasta_origem.rglob("*.pdf"))
        if arquivos_pdf:
            arquivo_encontrado = max(arquivos_pdf, key=os.path.getctime)
            logger.success(f"PDF baixado detectado: {arquivo_encontrado.name}")
            break
        time.sleep(1)

    if not arquivo_encontrado:
        raise TimeoutError("Timeout: Nenhum arquivo PDF foi encontrado na pasta de downloads ou subpastas.")

    time.sleep(5)
    fechar_leitor_pdf()
    time.sleep(1)

    #nome_final = f"SERASA_{id_item}.pdf"
    caminho_final = pasta_destino / arquivo_encontrado.name
    
    logger.info(f"Movendo '{arquivo_encontrado.name}' para '{caminho_final}'...")
    shutil.move(str(arquivo_encontrado), str(caminho_final))
    
    return str(caminho_final)

@retry(times=3, delay_s=2)
def baixar_relatorio_serasa(win_modulo, id_item: str, pasta_destino_final: str, cpf_cnpj, tipo_doc):
    """
    Executa o fluxo completo de download do relatório Serasa.
    """
    logger.info(f"Buscando cliente com documento '{cpf_cnpj}'...")
    acessar_cliente_por_cpf_cnpj(win_modulo, cpf_cnpj)

    logger.info(f"Acessando submódulo CONSULTAS EXTERNAS...")
    acessa_submodulo(win_modulo, "CONSULTAS EXTERNAS", plataforma="PLATAFORMA DE ATENDIMENTO")
    logger.info("Iniciando processo de download do relatório SERASA.")

    win_modulo.set_focus()
    try:
        # Mapeamento
        btn_serasa = ocr_path / "consultas_externas/serasa.png"
        btn_checkbox = ocr_path / "consultas_externas/score_de_credito.png"
        btn_consultar = ocr_path / "consultas_externas/consultar.png"
        btn_relatorios = ocr_path / "geral/impressora.png"
        btn_imprimir = ocr_path / "geral/imprimir.png"
        btn_bureau_credit = ocr_path / "consultas_externas/credit_bureau.png"

        # Passo 1 - Acessar SERASA 
        logger.info("Clicando no btn_serasa")
        click_and_verify(btn_serasa, btn_bureau_credit)

        # Se for CNPJ, faz o fluxo especial
        if tipo_doc == "CNPJ":
            logger.info("Documento é CNPJ, buscando campo credit_bureau.png para digitar 'Relato Gerencie'.")
            centro = pyautogui.locateCenterOnScreen(str(btn_bureau_credit), confidence=0.8)
            if centro:
                pyautogui.click(centro)
                time.sleep(0.5)
                pyautogui.hotkey('ctrl', 'a')
                time.sleep(0.2)
                pyautogui.press('backspace')
                time.sleep(0.2)
                pyautogui.write('Relato Gerencie', interval=0.05)
                logger.info("Campo credit_bureau preenchido com 'Relato Gerencie'.")
            else:
                raise RuntimeError("Campo credit_bureau.png não encontrado na tela.")

        if tipo_doc != "CNPJ":
            # Passo 2 - Marcar o checkbox
            logger.info("Marcando o checkbox do tipo de consulta")
            click_and_verify(btn_checkbox, btn_consultar)
        else:
            logger.info("Documento é CNPJ, ignorando a marcação do checkbox.")

        # Passo 3 - Clicar em 'Consultar'
        logger.info("Clicando em consultar")
        click_and_verify(btn_consultar,btn_relatorios)

        # Passo 4 - Verificar se o botão 'NOVA CONSULTA' existe
        try:
            logger.info("Verificando se é necessário clicar em 'NOVA CONSULTA'...")
            nova_consulta_btn = wait_for_element(win_modulo, **PLATAFORMA_DE_ATENDIMENTO["btn_nova_consulta"], timeout=10)
            if nova_consulta_btn.is_visible():
                logger.warning("Botão 'NOVA CONSULTA' encontrado. Clicando nele para prosseguir.")
                nova_consulta_btn.click_input()
        except TimeoutError:
            logger.info("Botão 'NOVA CONSULTA' não apareceu. Assumindo que a consulta prosseguiu diretamente.")

        # Passo 5 - Clicar em 'Relatórios'
        logger.info("Clicando em 'Relatórios'...")
        click_and_verify(btn_relatorios,btn_imprimir)

        # Passo 6: Clicar em 'Imprimir'
        logger.info("Clicando em 'Imprimir' para iniciar o download...")
        btn_imprimir_obj = wait_for_element(win_modulo, **PLATAFORMA_DE_ATENDIMENTO["btn_imprimir"], timeout=15)
        btn_imprimir_obj.click_input()

        # Passo 7: Gerenciar o download do arquivo PDF
        logger.info("Gerenciando o download do arquivo PDF...")
        pasta_download_temp = os.path.join(os.environ['USERPROFILE'], 'temp', 'relAssinc')
        caminho_final_relatorio = mover_relatorio_baixado(pasta_download_temp, pasta_destino_final, id_item)
        nome_final = f"Serasa_{id_item}_{cpf_cnpj}.pdf"
        novo_caminho = os.path.join(os.path.dirname(caminho_final_relatorio), nome_final)
        if os.path.exists(novo_caminho):
            os.remove(novo_caminho)
        os.rename(caminho_final_relatorio, novo_caminho)

        logger.success(f"Relatório SERASA salvo com sucesso em: {novo_caminho}")
        return novo_caminho
    except Exception as e:
        logger.error(f"Erro no fluxo SERASA: {e}")
        try:
            error_handler(win_modulo)
        except Exception as eh:
            logger.warning(f"Falha ao executar error_handler: {eh}")
        raise

@retry(times=3, delay_s=2)
def baixar_relatorio_bacen(win_modulo, id_item: str, pasta_destino_final: str, data_bacen: str, cpf_cnpj):
    """
    Executa o fluxo completo de download do relatório BACEN.
    """
    logger.info(f"Buscando cliente com documento '{cpf_cnpj}'...")
    acessar_cliente_por_cpf_cnpj(win_modulo, cpf_cnpj)

    logger.info(f"Acessando submódulo CONSULTAS EXTERNAS...")
    acessa_submodulo(win_modulo, "CONSULTAS EXTERNAS", plataforma="PLATAFORMA DE ATENDIMENTO")
    logger.info("Iniciando processo de download do relatório BACEN.")
    win_modulo.set_focus()
    try:
        # Mapeamento
        btn_serasa = ocr_path / "consultas_externas/bacen.png"
        btn_consultar = ocr_path / "consultas_externas/consultar.png"
        btn_sim = ocr_path / "consultas_externas/sim.png"
        btn_imprimir = ocr_path / "geral/imprimir.png"
        field_dados_consulta = ocr_path / "consultas_externas/dados_da_consulta.png"
        btn_relatorios = ocr_path / "geral/impressora.png"
        edit_data_base = ocr_path / "consultas_externas/data_base.png"

        # Passo 1 - Acessar SERASA 
        logger.info("Clicando no btn_serasa")
        click_and_verify(btn_serasa,btn_sim)

        # Passo 2 - Clicar em SIM
        logger.info("Clicando em sim")
        click_and_verify(btn_sim,btn_consultar)

        # Passo 3 - Digitar data-base
        _, pos = get_position_img(edit_data_base, offset_x=120, threshold=0.90)
        x, y = pos
        write_with_retry(x, y, data_bacen)

        # Passo 4 - Clicar em 'Consultar'
        logger.info("Clicando em consultar")
        click_and_verify(btn_consultar,field_dados_consulta)

        # Passo 5 - Verificar se o botão 'NOVA CONSULTA' existe
        try:
            logger.info("Verificando se é necessário clicar em 'NOVA CONSULTA'...")
            nova_consulta_btn = wait_for_element(win_modulo, **PLATAFORMA_DE_ATENDIMENTO["btn_nova_consulta"], timeout=10)
            if nova_consulta_btn.is_visible():
                logger.warning("Botão 'NOVA CONSULTA' encontrado. Clicando nele para prosseguir.")
                nova_consulta_btn.click_input()
        except TimeoutError:
            logger.info("Botão 'NOVA CONSULTA' não apareceu. Assumindo que a consulta prosseguiu diretamente.")

        # Passo 6 - Clicar em 'Relatórios'
        logger.info("Clicando em 'Relatórios'...")
        click_and_verify(btn_relatorios,btn_imprimir)

        # Passo 7: Clicar em 'Imprimir'
        logger.info("Clicando em 'Imprimir' para iniciar o download...")
        btn_imprimir_obj = wait_for_element(win_modulo, **PLATAFORMA_DE_ATENDIMENTO["btn_imprimir"], timeout=15)
        btn_imprimir_obj.click_input()

        # Passo 7: Gerenciar o download do arquivo PDF
        logger.info("Gerenciando o download do arquivo PDF...")
        pasta_download_temp = os.path.join(os.environ['USERPROFILE'], 'temp', 'relAssinc')
        caminho_final_relatorio = mover_relatorio_baixado(pasta_download_temp, pasta_destino_final, id_item)
        nome_final = f"Bacen_{id_item}_{cpf_cnpj}.pdf"
        novo_caminho = os.path.join(os.path.dirname(caminho_final_relatorio), nome_final)
        if os.path.exists(novo_caminho):
            os.remove(novo_caminho)
        os.rename(caminho_final_relatorio, novo_caminho)

        logger.success(f"Relatório BACEN salvo com sucesso em: {novo_caminho}")
        return novo_caminho
    except Exception as e:
        logger.error(f"Erro no fluxo BACEN: {e}")
        try:
            error_handler(win_modulo)
        except Exception as eh:
            logger.warning(f"Falha ao executar error_handler: {eh}")
        raise

@retry(times=3, delay_s=2)
def baixar_relatorio_faturamento_renda(win_modulo, id_item: str, pasta_destino_final: str, cpf_cnpj, cooperativa: str, tipo_doc: str):
    """
    Executa o fluxo completo de download do relatório de Faturamento/Renda.
    """
    try:
        logger.info(f"Buscando cliente com documento '{cpf_cnpj}'...")
        acessar_cliente_por_cpf_cnpj(win_modulo, cpf_cnpj)

        # Decidir submódulo conforme tipo do documento
        if tipo_doc == 'CNPJ':
            submodulo_faturamento = 'FATURAMENTO'
        elif tipo_doc == 'CPF':
            submodulo_faturamento = 'RENDAS'
        else:
            logger.error(f"Tipo de documento desconhecido para {cpf_cnpj}, não é possível determinar o submódulo.")
            raise RuntimeError("Tipo de documento inválido para baixar relatório de Faturamento/Renda.")
        
        logger.info(f"Acessando submódulo '{submodulo_faturamento}'...")
        acessa_submodulo(win_modulo, submodulo_faturamento, plataforma="PLATAFORMA DE ATENDIMENTO")
        time.sleep(3)
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

        relatorios_por_renda = []

        if not pontos_relatorio_renda:
            logger.info("Nenhuma renda encontrada na tela.")
            try:
                error_handler(win_modulo)
            except Exception as e:
                logger.warning(f"Falha ao executar error_handler: {e}")
            raise RuntimeError("Nenhuma renda encontrada na tela. Tentando novamente...")
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
                try:
                    error_handler(win_modulo)
                except Exception as e:
                    logger.warning(f"Falha ao executar error_handler: {e}")
                raise RuntimeError("Nenhum relatório encontrado após clicar na renda. Tentando novamente...")
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
                if os.path.exists(novo_caminho):
                    os.remove(novo_caminho)
                os.rename(caminho_final_relatorio, novo_caminho)
                logger.info(f"Relatório renomeado para: {novo_caminho}")
                caminhos_baixados_dict[(idx_renda, idx_rel)] = novo_caminho
        logger.success("Relatórios Faturamento/Renda salvos com sucesso.")
        return caminhos_baixados_dict
    except Exception as e:
        logger.error(f"Erro no fluxo RENDAS: {e}")
        try:
            error_handler(win_modulo)
        except Exception as eh:
            logger.warning(f"Falha ao executar error_handler: {eh}")
        raise
@retry(times=3, delay_s=2)
def baixar_relatorio_conta_corrente(win_modulo, id_item: str, pasta_destino_final: str, cpf_cnpj: str):
    """
    Executa o fluxo completo de download do relatório de Conta Corrente.
    """
    try:
        logger.info(f"Buscando cliente com documento '{cpf_cnpj}'...")
        acessar_cliente_por_cpf_cnpj(win_modulo, cpf_cnpj)
        logger.info(f"Acessando submódulo CONSULTAS EXTERNAS...")
        acessa_submodulo(win_modulo, "SALDO", plataforma="PLATAFORMA DE ATENDIMENTO")
        logger.info("Iniciando processo de download do relatório Conta Corrente.")
        win_modulo.set_focus()

        caminho_img_verificacao = ocr_path / 'conta_corrente' / 'verificacao.png'
        caminho_img_voltar = ocr_path / 'conta_corrente' / 'voltar.png'

        logger.info("Verificando se o campo muda de cor ao clicar no centro do retângulo...")
        caminhos_prints = []
        for idx, coord in enumerate(RETANGULOS_CONTACORRENTE_RECT):
            # Calcula as coordenadas do centro do retângulo definido por 'coord'
            x = (coord['l'] + coord['r']) // 2
            y = (coord['t'] + coord['b']) // 2
            if verificar_campo_muda_de_cor(coord):
                logger.info(f"Retângulo {idx+1} centro (x={x}, y={y}) é CLICÁVEL (mudou de cor ao clicar). Realizando duplo clique...")
                double_click_coords(x, y)
                time.sleep(0.5)
                # Aguarda o elemento de verificação aparecer antes de prosseguir
                
                timeout_verificacao = 10  # segundos
                t0 = time.time()
                while True:
                    pos_verificacao = get_position_img(str(caminho_img_verificacao), threshold=0.8, timeout=2)
                    if pos_verificacao:
                        logger.info(f"Elemento de verificação encontrado na tela: {caminho_img_verificacao}")
                        break
                    elif time.time() - t0 > timeout_verificacao:
                        logger.error("Timeout ao aguardar o elemento de verificação aparecer na tela!")
                        try:
                            error_handler(win_modulo)
                        except Exception as e:
                            logger.warning(f"Falha ao executar error_handler: {e}")
                        raise RuntimeError("Timeout ao aguardar o elemento de verificação aparecer na tela!")
                    else:
                        logger.info("Elemento de verificação ainda não apareceu, aguardando...")
                        time.sleep(0.5)

                # Salva o print
                caminho_print = salvar_print_regiao(*REGIAO_PRINT, pasta_destino_final)
                # Após tirar o print, clicar no botão voltar
                
                timeout_voltar = 10  # segundos
                t0 = time.time()
                while True:
                    pos_voltar = get_position_img(str(caminho_img_voltar), threshold=0.8, timeout=2)
                    if pos_voltar:
                        _, (xv, yv) = pos_voltar
                        logger.info(f"Clicando no botão voltar em ({xv}, {yv})")
                        pyautogui.click(xv, yv)
                        time.sleep(0.5)
                        break
                    elif time.time() - t0 > timeout_voltar:
                        logger.error("Timeout ao aguardar o botão voltar aparecer na tela!")
                        try:
                            error_handler(win_modulo)
                        except Exception as e:
                            logger.warning(f"Falha ao executar error_handler: {e}")
                        raise RuntimeError("Timeout ao aguardar o botão voltar aparecer na tela!")
                    else:
                        logger.info("Botão voltar ainda não apareceu, aguardando...")
                        time.sleep(0.5)

                caminhos_prints.append(str(caminho_print))

            else:
                logger.warning(f"Retângulo {idx+1} centro (x={x}, y={y}) NÃO mudou de cor ao clicar. Fim da lista de contas.")
                break
            time.sleep(0.3)
        # Renomeia todos os prints de Conta Corrente no final, igual ao faturamento/renda
        caminhos_baixados_dict = {}
        if not caminhos_prints:
            logger.error("Nenhum print de Conta Corrente foi gerado. Tentando novamente...")
            try:
                error_handler(win_modulo)
            except Exception as e:
                logger.warning(f"Falha ao executar error_handler: {e}")
            raise RuntimeError("Nenhum print de Conta Corrente foi gerado. Tentando novamente...")
        for idx, caminho in enumerate(caminhos_prints):
            nome_final = f"ContaCorrente_{idx}_{id_item}.png"
            novo_caminho = os.path.join(os.path.dirname(caminho), nome_final)
            if os.path.exists(novo_caminho):
                os.remove(novo_caminho)
            os.rename(caminho, novo_caminho)
            logger.info(f"Print renomeado para: {novo_caminho}")
            caminhos_baixados_dict[(idx, 0)] = novo_caminho
        logger.success("Relatórios Conta Corrente salvos com sucesso.")
        return caminhos_baixados_dict
    except Exception as e:
        logger.error(f"Erro no fluxo CONTA CORRENTE: {e}")
        try:
            error_handler(win_modulo)
        except Exception as eh:
            logger.warning(f"Falha ao executar error_handler: {eh}")
        raise

@retry(times=3, delay_s=2)
def baixar_relatorio_painel_comercial(win_modulo, id_item: str, pasta_destino_final: str, cpf_cnpj):
    """
    Baixa os relatórios AnaliseConsolidada e FichaDetalhada do módulo PAINEL COMERCIAL.
    """
    fechar_leitor_pdf()
    logger.info("Acessando o módulo 'PAINEL COMERCIAL'...")
    win_painel_comercial = acessar_modulo(win_modulo, "PAINEL COMERCIAL", 5)
    if not win_painel_comercial:
        raise RuntimeError("Falha ao obter a janela do módulo 'PAINEL COMERCIAL'.")
    time.sleep(3)
    logger.info("Iniciando download dos relatórios do PAINEL COMERCIAL...")
    win_painel_comercial.set_focus()
    
    # Caminho dos templates
    current_file = Path(__file__).resolve()
    lib_project_root = current_file.parent.parent
    ocr_painel_comercial = (lib_project_root / "src" / "lib_sisbr_desktop" / "ocr" / "painel_comercial").resolve()
    
    relatorios_baixados = {}
    
    try:
        # Aguardar a imagem pesquisar aparecer
        logger.info("Aguardando a tela de pesquisa aparecer...")
        template_pesquisar = ocr_painel_comercial / "pesquisar.png"
        result_pesquisar = get_position_img(template_pesquisar, threshold=0.87, timeout=30)
        if not result_pesquisar:
            raise RuntimeError("Tela de pesquisa não apareceu no timeout especificado")
        
        logger.success("Tela de pesquisa encontrada!")
        
        # Clicar no campo CPF/CNPJ e inserir o documento
        logger.info(f"Inserindo CPF/CNPJ: {cpf_cnpj}")
        template_campo_cpfcnpj = ocr_painel_comercial / "campo_cpfcnpj.png"
        
        # Usar click_and_verify para clicar no campo e verificar se o documento foi inserido
        success = click_and_verify(
            img_click=template_campo_cpfcnpj,
            img_verify=template_pesquisar,  # Verifica se ainda está na tela de pesquisa
            offset_x=None,
            offset_y=None,
            click_threshold=0.87,
            verify_threshold=0.87,
            click_timeout=10,
            verify_timeout=5,
            total_timeout=30,
            delay_after_click=0.5
        )
        
        if success:
            # Inserir o CPF/CNPJ com verificação que aceita formatação automática
            # Usar coordenadas do campo CPF/CNPJ e função do helpers
            coord_campo_cpfcnpj = {'l': 807, 't': 421, 'w': 410, 'h': 36}
            # Converter de l,t,w,h para l,t,r,b
            coord_rect = {
                'l': coord_campo_cpfcnpj['l'],
                't': coord_campo_cpfcnpj['t'],
                'r': coord_campo_cpfcnpj['l'] + coord_campo_cpfcnpj['w'],
                'b': coord_campo_cpfcnpj['t'] + coord_campo_cpfcnpj['h']
            }
            
            logger.info(f"Clicando no centro do campo CPF/CNPJ usando helpers...")
            # Usar verificar_campo_muda_de_cor para clicar no centro do retângulo
            verificar_campo_muda_de_cor(coord_rect, delay_clique=0.5)
            
            # Agora inserir o texto usando as coordenadas do centro
            x_centro = (coord_rect['l'] + coord_rect['r']) // 2
            y_centro = (coord_rect['t'] + coord_rect['b']) // 2
            write_with_retry_formatted(x_centro, y_centro, cpf_cnpj)
            logger.success(f"CPF/CNPJ {cpf_cnpj} inserido e verificado com sucesso")
            
            # Clicar no botão pesquisar
            logger.info("Pressionando Enter para pesquisar...")
            pyautogui.press('enter')
            time.sleep(2)
            
            
            if len(cpf_cnpj) == 11:  # CPF
                logger.info("Documento identificado como CPF, buscando imagem 'pessoa_fisica.png'")
                template_pessoa = ocr_painel_comercial / "pessoa_fisica.png"
            elif len(cpf_cnpj) == 14:  # CNPJ
                logger.info("Documento identificado como CNPJ, buscando imagem 'pessoa_juridica.png'")
                template_pessoa = ocr_painel_comercial / "pessoa_juridica.png"
            else:
                logger.error(f"Documento {cpf_cnpj} não é um CPF ou CNPJ válido")
                raise ValueError(f"Documento {cpf_cnpj} não é um CPF ou CNPJ válido")
            
            # Buscar e clicar na imagem correspondente
            logger.info(f"Procurando pela imagem: {template_pessoa.name}")
            resultado_pessoa = get_position_img(str(template_pessoa), timeout=10)
            
            if resultado_pessoa:
                logger.info(f"Imagem {template_pessoa.name} encontrada, clicando nela")
                pyautogui.click(resultado_pessoa[1])
                time.sleep(1)
            
            # Aguardar e clicar no campo relatório
            logger.info("Aguardando o campo relatório aparecer...")
            template_relatorio = ocr_painel_comercial / "relatorios.png"
            result_relatorio = get_position_img(template_relatorio, threshold=0.87, timeout=30)
            if not result_relatorio:
                raise RuntimeError("Campo relatório não apareceu no timeout especificado")
            
            _, (x_relatorio, y_relatorio) = result_relatorio
            logger.info(f"Campo relatório encontrado em ({x_relatorio}, {y_relatorio})")
            pyautogui.click(x_relatorio, y_relatorio)
            time.sleep(1)
            
            # Clicar no relatório FichaDetalhada
            logger.info("Clicando no relatório FichaDetalhada...")
            template_fichadetalhada = ocr_painel_comercial / "fichadetalhada.png"
            result_fichadetalhada = get_position_img(template_fichadetalhada, threshold=0.87, timeout=30)
            if not result_fichadetalhada:
                raise RuntimeError("Relatório FichaDetalhada não encontrado")
            
            _, (x_ficha, y_ficha) = result_fichadetalhada
            logger.info(f"Relatório FichaDetalhada encontrado em ({x_ficha}, {y_ficha})")
            pyautogui.click(x_ficha, y_ficha)
            time.sleep(3)  # Aguardar o download iniciar
            
            # Aguardar e mover o arquivo baixado
            logger.info("Aguardando download do relatório FichaDetalhada...")
            downloads_path = Path.home() / "Downloads"
            timeout_download = 60  # 60 segundos para aguardar o download
            start_time = time.time()
            
            while time.time() - start_time < timeout_download:
                # Procurar por arquivos que começam com "Ficha-Detalhada-"
                ficha_files = list(downloads_path.glob("Ficha-Detalhada-*.pdf"))
                if ficha_files:
                    # Pegar o arquivo mais recente
                    latest_file = max(ficha_files, key=lambda f: f.stat().st_mtime)
                    file_age = time.time() - latest_file.stat().st_mtime
                    
                    # Se o arquivo foi criado/modificado nos últimos 10 segundos, é provavelmente o nosso
                    if file_age < 10:
                        # Mover para a pasta temp
                        novo_nome = f"FichaDetalhada_{id_item}_{cpf_cnpj}.pdf"
                        destino = Path(pasta_destino_final) / novo_nome
                        destino.parent.mkdir(parents=True, exist_ok=True)
                        
                        try:
                            import shutil
                            shutil.move(str(latest_file), str(destino))
                            relatorios_baixados["FichaDetalhada"] = str(destino)
                            logger.success(f"Relatório FichaDetalhada movido para: {destino}")
                            break
                        except Exception as e:
                            logger.error(f"Erro ao mover arquivo: {e}")
                            raise
                
                time.sleep(1)
            else:
                logger.warning("Timeout aguardando download do relatório FichaDetalhada")
            
            # Colocar foco na janela do navegador antes do próximo download
            logger.info("Colocando foco na janela do navegador...")
            win_painel_comercial.set_focus()
            time.sleep(1)
            
            # Clicar no relatório AnaliseConsolidada
            logger.info("Clicando no relatório AnaliseConsolidada...")
            template_analiseconsolidada = ocr_painel_comercial / "analiseconsolidada.png"
            result_analiseconsolidada = get_position_img(template_analiseconsolidada, threshold=0.87, timeout=30)
            if not result_analiseconsolidada:
                raise RuntimeError("Relatório AnaliseConsolidada não encontrado")
            
            _, (x_analise, y_analise) = result_analiseconsolidada
            logger.info(f"Relatório AnaliseConsolidada encontrado em ({x_analise}, {y_analise})")
            pyautogui.click(x_analise, y_analise)
            time.sleep(3)  # Aguardar o download iniciar
            
            # Aguardar e mover o arquivo baixado
            logger.info("Aguardando download do relatório AnaliseConsolidada...")
            start_time = time.time()
            
            while time.time() - start_time < timeout_download:
                # Procurar por arquivos que começam com "Analise-Consolidada-"
                analise_files = list(downloads_path.glob("Analise-Consolidada-*.pdf"))
                if analise_files:
                    # Pegar o arquivo mais recente
                    latest_file = max(analise_files, key=lambda f: f.stat().st_mtime)
                    file_age = time.time() - latest_file.stat().st_mtime
                    
                    # Se o arquivo foi criado/modificado nos últimos 10 segundos, é provavelmente o nosso
                    if file_age < 10:
                        # Mover para a pasta temp
                        novo_nome = f"AnaliseConsolidada_{id_item}_{cpf_cnpj}.pdf"
                        destino = Path(pasta_destino_final) / novo_nome
                        destino.parent.mkdir(parents=True, exist_ok=True)
                        
                        try:
                            import shutil
                            shutil.move(str(latest_file), str(destino))
                            relatorios_baixados["AnaliseConsolidada"] = str(destino)
                            logger.success(f"Relatório AnaliseConsolidada movido para: {destino}")
                            break
                        except Exception as e:
                            logger.error(f"Erro ao mover arquivo: {e}")
                            raise
                
                time.sleep(1)
            else:
                logger.warning("Timeout aguardando download do relatório AnaliseConsolidada")
            
            # Fechar o Chrome após baixar os relatórios
            logger.info("Fechando o Chrome após download dos relatórios...")
            fechar_leitor_pdf()
            time.sleep(1)
            
            return relatorios_baixados
    except Exception as e:
        logger.error(f"Erro ao baixar relatórios do PAINEL COMERCIAL: {e}")
        # Fechar o Chrome mesmo em caso de erro
        try:
            error_handler(win_painel_comercial)
        except Exception as eh:
            logger.warning(f"Falha ao executar error_handler: {eh}")
            logger.info("Fechando o Chrome devido a erro...")
            fechar_leitor_pdf()
            raise

@retry(times=3, delay_s=2)
def baixar_relatorio_lancamentos(win_modulo, id_item: str, pasta_destino_final: str, cpf_cnpj: str, numero_conta: str):
    """
    Baixa o relatório de lançamentos do módulo CONTA CORRENTE.
    """
    logger.info("Garantindo que 'PLATAFORMA DE CRÉDITO' não esteja aberta previamente...")
    fechar_modulo(win_modulo, "CONTA CORRENTE")
    logger.info("Acessando o módulo 'CONTA CORRENTE'...")
    win_conta_corrente = acessar_modulo(win_modulo, "CONTA CORRENTE", 5)
    if not win_conta_corrente:
        raise RuntimeError("Falha ao obter a janela do módulo 'CONTA CORRENTE'.")
    time.sleep(3)

    logger.info("Iniciando download do relatório de LANÇAMENTOS...")
    win_conta_corrente.set_focus()
    ocr_lancamentos = (lib_project_root / "src" / "lib_sisbr_desktop" / "ocr" / "conta_corrente").resolve()

    btn_relatorio = ocr_lancamentos / "relatorio.png"
    btn_relatorio_lancamentos = ocr_lancamentos / "relatorio_de_lancamentos.png"
    btn_ok = ocr_lancamentos / "ok.png"
    btn_imprimir = ocr_lancamentos / "imprimir.png"

    try:
        # Passo 1 - Clicar em "Relatório"
        logger.info("Clicando em 'Relatório'...")

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
        write_with_retry_formatted(x_centro_inicial, y_centro_inicial, numero_conta)  # Substitua pelo número da conta real
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
        write_with_retry_formatted(x_centro_final, y_centro_final, numero_conta)  # Substitua pelo número da conta real
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
            time.sleep(0.4)
            
            logger.success(f"Código {codigo} inserido e adicionado com sucesso")
        
        logger.success(f"Todos os {len(codigos)} códigos foram inseridos com sucesso")
        
        # Passo 10 - Clicar no botão OK
        logger.info("Clicando no botão OK...")
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
        from tests.etapa_downloads import mover_relatorio_baixado
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
        try:
            error_handler(win_conta_corrente)
        except Exception as eh:
            logger.warning(f"Falha ao executar error_handler: {eh}")
            logger.error(f"Erro ao baixar relatório de LANÇAMENTOS: {e}")
            raise

@retry(times=3, delay_s=2)
def baixar_sumula_credito(win_modulo, id_item: str, pasta_destino_final: str, numero_proposta: str, produto: str):
    """
    Baixa a súmula de crédito do módulo de CRÉDITO usando o número da proposta.
    """
    logger.info("Garantindo que 'PLATAFORMA DE CRÉDITO' não esteja aberta previamente...")
    fechar_modulo(win_modulo, "PLATAFORMA DE CRÉDITO")
    logger.info("Acessando o módulo 'PLATAFORMA DE CRÉDITO'...")
    win_credito = acessar_modulo(win_modulo, "PLATAFORMA DE CRÉDITO", 5)
    if not win_credito:
        raise RuntimeError("Falha ao obter a janela do módulo 'PLATAFORMA DE CRÉDITO'.")
    time.sleep(3)

    logger.info(f"Acessando submódulo '{produto}'...")
    acessa_submodulo(win_credito, produto, plataforma="PLATAFORMA DE CRÉDITO")
    logger.info("Iniciando download da SÚMULA DE CRÉDITO...")
    win_credito.set_focus()

    ocr_credito = (lib_project_root / "src" / "lib_sisbr_desktop" / "ocr" / "plataforma_de_credito").resolve()

    try:
        # Passo 1 - Acessar o módulo de Crédito
        logger.info("Acessando o módulo de Crédito...")
        # Clicar em Operações de Crédito
        btn_operacoes_credito = ocr_credito / "operacoes_credito.png"
        btn_operacao_credito_consignado = ocr_credito / "operacao_credito_consignado.png"
        btn_operacao_credito_credito_rural = ocr_credito / "operacoes_credito_rural.png"
        bnt_antecipacao = ocr_credito / "antecipacao.png"
        bnt_recebiveis = ocr_credito / "recebiveis.png"
        btn_mesa_operacoes = ocr_credito / "mesa_operacoes.png"
        btn_verify = ocr_credito / "menu_mesa_de_operacoes.png"

        if produto == "EMPRÉSTIMO":
            logger.info("Clicando em 'Operações de Crédito'...")
            click_and_verify(btn_operacoes_credito, btn_mesa_operacoes)

        elif produto == "CONCESSÃO DE LIMITES":
            logger.info("Clicando em 'ANTECIPAÇÃO'...")
            click_and_verify(bnt_antecipacao, bnt_recebiveis)
            logger.info("Clicando em 'RECEBÍVEIS'...")
            click_and_verify(bnt_recebiveis, btn_mesa_operacoes)

        elif produto == "CONSIGNADO":
            logger.info("Clicando em 'Operações de Crédito consignado'...")
            click_and_verify(btn_operacao_credito_consignado, btn_mesa_operacoes)

        elif produto == "CRÉDITO RURAL":
            logger.info("Clicando em 'Operações de Crédito rural'...")
            click_and_verify(btn_operacao_credito_credito_rural, btn_mesa_operacoes)

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
        write_with_retry(coord_x_proposta, coord_y_proposta, numero_proposta)  # Número da proposta
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
        try:
            error_handler(win_credito)
        except Exception as eh:
            logger.warning(f"Falha ao executar error_handler: {eh}")
        raise
    
@retry(times=3, delay_s=2)
def baixar_relatorio_carteira_cadente(win_modulo, id_item: str, pasta_destino_final: str, associado_desde: str, cpf_cnpj: str, produto: str):
    """
    Executa o fluxo completo de download do relatório de Carteira Cadente.
    """
    logger.info("Garantindo que 'PLATAFORMA DE CRÉDITO' não esteja aberta previamente...")
    fechar_modulo(win_modulo, "PLATAFORMA DE CRÉDITO")
    logger.info("Acessando o módulo 'PLATAFORMA DE CRÉDITO' para baixar a Carteira Cadente...")
    win_credito = acessar_modulo(win_modulo, "PLATAFORMA DE CRÉDITO", 5)

    if not win_credito:
        raise RuntimeError("Falha ao obter a janela do módulo 'PLATAFORMA DE CRÉDITO'.")
    time.sleep(3)

    logger.info(f"Acessando submódulo '{produto}'...")
    acessa_submodulo(win_credito, "CONCESSÃO DE LIMITES", plataforma="PLATAFORMA DE CRÉDITO")
    logger.info("Iniciando processo de download do relatório Carteira Cadente.")
    win_credito.set_focus()

    try:
        # Caminho dos templates de crédito
        caminho_templates_credito = (lib_project_root / "src" / "lib_sisbr_desktop" / "ocr" / "plataforma_de_credito").resolve()
        
        # Organizar todas as imagens no começo da função com nomenclatura clara
        btn_antecipacao = caminho_templates_credito / "antecipacao.png"
        btn_recebiveis = caminho_templates_credito / "recebiveis.png"
        btn_limites_liberados = caminho_templates_credito / "limites_liberados.png"
        btn_procurar = caminho_templates_credito / "procurar.png"
        btn_sem_limites = caminho_templates_credito / "sem_limites.png"
        img_conducao = caminho_templates_credito / "conducao.png"
        img_consulta_carteira = caminho_templates_credito / "consulta_carteira.png"
        btn_pesquisar = caminho_templates_credito / "pesquisar.png"
        consulta_ancora_img = ocr_credito / "consulta_ancora.png"

        # Passo 1: Clicar em "Antecipação" e verificar "Recebíveis"
        logger.info("Clicando em 'Antecipação' e verificando 'Recebíveis'...")
        click_and_verify(btn_antecipacao, btn_recebiveis)
        time.sleep(0.6)  # Aguarda processamento da navegação

        # Passo 2: Clicar em "Recebíveis" e verificar "Limites Liberados"
        logger.info("Clicando em 'Recebíveis' e verificando 'Limites Liberados'...")
        click_and_verify(btn_recebiveis, btn_limites_liberados)
        time.sleep(0.6)  # Aguarda processamento da navegação

        # Passo 3: Clicar em "Limites Liberados"
        logger.info("Clicando em 'Limites Liberados'...")
        pyautogui.click(get_position_img(str(btn_limites_liberados))[1])
        time.sleep(0.8)  # Aguarda carregamento da tela de limites
        
        # Obter coordenadas do mapeamento para campo CPF/CNPJ
        coordenadas_campo_cpf_cnpj = PLATAFORMA_DE_CREDITO["campo_cpf_cnpj"]["bounds"]
        coord_x_cpf_cnpj, coord_y_cpf_cnpj = coordenadas_campo_cpf_cnpj[0], coordenadas_campo_cpf_cnpj[1]

        logger.info(f"Clicando e digitando '{cpf_cnpj}' na coordenada ({coord_x_cpf_cnpj}, {coord_y_cpf_cnpj}) usando write_with_retry...")
        write_with_retry(coord_x_cpf_cnpj, coord_y_cpf_cnpj, cpf_cnpj)
        time.sleep(0.5)  # Aguarda digitação completa
        pyautogui.press('tab')
        time.sleep(0.6)  # Aguarda mudança de campo
        
        # Inserir a data nas coordenadas do mapeamento
        time.sleep(2)
        coordenadas_campo_data_associado = PLATAFORMA_DE_CREDITO["campo_data_associado"]["bounds"]
        coord_x_data_associado, coord_y_data_associado = coordenadas_campo_data_associado[0], coordenadas_campo_data_associado[1]
        
        logger.info(f"Clicando no campo de data em ({coord_x_data_associado}, {coord_y_data_associado}) e inserindo a data '{associado_desde}'...")
        write_with_retry(coord_x_data_associado, coord_y_data_associado, associado_desde)
        time.sleep(0.5)  # Aguarda digitação completa

        # Clicar na imagem do botão "Procurar"
        logger.info("Clicando no botão 'Procurar'...")
        pyautogui.doubleClick(get_position_img(str(btn_procurar))[1], interval=1)
        time.sleep(0.8)  # Aguarda processamento da pesquisa
        
        # Após clicar em "Procurar", verificar se aparece o pop-up "sem_limites"
        time.sleep(2)  # Aguarda um pouco para o pop-up aparecer, se for o caso

        pos_sem_limites = get_position_img(str(btn_sem_limites), timeout=6)
        if pos_sem_limites is not None:
            logger.warning("Pop-up 'Sem Limites' detectado na tela! Nenhum limite disponível para este cliente.")
            return None  # Retorna None, pois não há relatórios para baixar 
        else:
            logger.info("Limites encontrados, prosseguindo com o download dos relatórios.")
            pyautogui.press('esc')
            time.sleep(0.6)  # Aguarda fechamento do pop-up


            time.sleep(3)
            logger.info(f"Acessando submódulo 'RECEBÍVEIS'...")
            acessa_submodulo(win_credito, "RECEBÍVEIS", plataforma="PLATAFORMA DE CRÉDITO")
            time.sleep(0.8)  # Aguarda carregamento do submódulo
            
            # Clicar na imagem "conducao" e verificar a imagem "consulta_carteira" usando click_and_verify
            logger.info("Clicando na imagem 'conducao' e verificando a imagem 'consulta_carteira'...")

            click_and_verify(img_conducao, img_consulta_carteira)
            time.sleep(0.6)  # Aguarda processamento da navegação
            pyautogui.click(get_position_img(str(img_consulta_carteira))[1])
            time.sleep(0.8)  # Aguarda carregamento da tela de consulta
            
            # Verificação simples para aguardar a imagem consulta_ancora
            logger.info("Verificando se a imagem consulta_ancora está na tela...")

            pos_consulta = get_position_img(consulta_ancora_img, threshold=0.85, timeout=10)
            if not pos_consulta:
                logger.error("Imagem consulta_ancora não encontrada!")
                raise RuntimeError("Imagem consulta_ancora não encontrada na tela!")
            logger.info("Imagem consulta_ancora encontrada. Prosseguindo...")
            
            # Usar coordenadas do mapeamento para campo CPF/CNPJ da carteira
            bounds = PLATAFORMA_DE_CREDITO["campo_cpf_cnpj_carteira"]["bounds"]
            left, top, right, bottom = bounds
            center_x = (left + right) // 2
            center_y = (top + bottom) // 2
            write_without_verify(center_x, center_y, cpf_cnpj)
            time.sleep(0.6)  # Aguarda digitação completa
            pyautogui.press('tab')
            time.sleep(1)  # Wait for 1 second after tab press
            logger.info("Inserindo data de início...")
            
            # Calcula a data de hoje menos 90 dias
            data_inicio_90_dias_atras = (datetime.now() - timedelta(days=90)).strftime("%d/%m/%Y")
            
            # Usar coordenadas do mapeamento para campo data início
            bounds = PLATAFORMA_DE_CREDITO["campo_data_inicio"]["bounds"]
            left, top, right, bottom = bounds
            center_x = (left + right) // 2
            center_y = (top + bottom) // 2
            logger.info(f"Inserindo data de início: {data_inicio_90_dias_atras}")
            write_without_verify(center_x, center_y, data_inicio_90_dias_atras)
            time.sleep(0.6)  # Aguarda digitação completa

            # Usar coordenadas do mapeamento para campo data fim
            bounds = PLATAFORMA_DE_CREDITO["campo_data_fim"]["bounds"]
            left, top, right, bottom = bounds
            center_x = (left + right) // 2
            center_y = (top + bottom) // 2
            data_fim_hoje = datetime.now().strftime("%d/%m/%Y")
            logger.info(f"Inserindo data de fim: {data_fim_hoje}")
            write_without_verify(center_x, center_y, data_fim_hoje)
            time.sleep(0.6)  # Aguarda digitação completa
            
            logger.info("Clicando no botão pesquisar...")
            pesquisar_pos = get_position_img(str(btn_pesquisar))
            if pesquisar_pos:
                pyautogui.click(pesquisar_pos[1])
            else:
                logger.error("Botão pesquisar não encontrado!")
                raise RuntimeError("Botão pesquisar não encontrado na tela!")
            time.sleep(0.8)  # Aguarda processamento da pesquisa e carregamento dos resultados
            # Tirar print usando coordenadas do mapeamento
            coordenadas_regiao_print = PLATAFORMA_DE_CREDITO["regiao_print"]["bounds"]
            time.sleep(0.5)  # Aguarda estabilização da tela antes de capturar o print
            caminho_arquivo_print = salvar_print_regiao(
                left=coordenadas_regiao_print[0],
                top=coordenadas_regiao_print[1],
                right=coordenadas_regiao_print[2],
                bottom=coordenadas_regiao_print[3],
                pasta_destino=pasta_destino_final,
                nome_prefixo=f"CarteiraCadente_{id_item}_"
            )

            logger.info(f"Print do retângulo {coordenadas_regiao_print} salvo em: {caminho_arquivo_print}")
            time.sleep(0.5)  # Aguarda finalização do salvamento
            return caminho_arquivo_print
    except Exception as e:
        logger.error(f"Erro ao baixar relatório Carteira Cadente: {e}")
        try:
            error_handler(win_modulo)
        except Exception as eh:
            logger.warning(f"Falha ao executar error_handler: {eh}")
        raise

@retry(times=3, delay_s=2)
def baixar_relatorio_liquidacoes_baixas(win_modulo, id_item: str, pasta_destino_final: str, cpf_cnpj: str):
    """
    Executa o fluxo completo de download do relatório de lIQUIDAÇÕES BAIXAS.
    """
    fechar_leitor_pdf()
    logger.info("Acessando o módulo 'COBRANÇA BANCÁRIA 3.0'...")
    win_cobranca = acessar_modulo(win_modulo, "COBRANÇA BANCÁRIA 3.0", 5)
    if not win_cobranca:
        raise RuntimeError("Falha ao obter a janela do módulo 'COBRANÇA BANCÁRIA 3.0'.")
    time.sleep(3)
    logger.info("Iniciando download dos relatórios do COBRANÇA BANCÁRIA 3.0...")
    win_cobranca.set_focus()
    logger.info("Iniciando processo de download do relatório lIQUIDAÇÕES BAIXAS.")

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
                fechar_leitor_pdf()
            
            _, coords_gerar = resultado_gerar
            pyautogui.click(coords_gerar)
            time.sleep(1.0)  # Aguardar o relatório ser gerado
            
            logger.info("Sequência de cliques para gerar relatório concluída com sucesso!")
            
            # Aguardar a imagem "impressora" aparecer e clicar nela
            logger.info("Aguardando a imagem 'impressora' aparecer...")
            resultado_impressora = get_position_img(btn_impressora, timeout=30)  # Timeout maior para aguardar geração
            if not resultado_impressora:
                raise RuntimeError("Imagem 'impressora' não apareceu após gerar relatório")
                fechar_leitor_pdf()
            
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
                fechar_leitor_pdf()
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
                                fechar_leitor_pdf()
                                # Retornar o caminho do relatório baixado
                                return relatorio
                                
                            except Exception as e:
                                logger.error(f"Erro ao mover arquivo: {e}")
                                raise
                    
                    time.sleep(1)
                else:
                    logger.warning("Timeout aguardando download do relatório Movimento_de_Liquidacoes")
                    fechar_leitor_pdf()
                    return None
    except Exception as e:
        logger.error(f"Erro ao baixar relatórios do PAINEL COMERCIAL: {e}")
        # Fechar o Chrome mesmo em caso de erro
        try:
            error_handler(win_cobranca)
        except Exception as eh:
            logger.warning(f"Falha ao executar error_handler: {eh}")
            logger.info("Fechando o Chrome devido a erro...")
            fechar_leitor_pdf()
            raise

@retry(times=3, delay_s=2)
def baixar_relatorio_liquidacoes_slc(win_modulo, id_item: str, pasta_destino_final: str, cpf_cnpj):
    """
    Baixa o relatório de lançamentos do módulo LIQUIDAÇÕES SLC.
    """
    logger.info("Acessando o módulo 'PLATAFORMA DE CREDENCIAMENTO'...")
    win_credenciamento = acessar_modulo(win_modulo, "PLATAFORMA DE CREDENCIAMENTO", 5)
    if not win_credenciamento:
        raise RuntimeError("Falha ao obter a janela do módulo 'PLATAFORMA DE CREDENCIAMENTO'.")
    time.sleep(3)

    logger.info("Iniciando download do relatório de LANÇAMENTOS...")
    win_credenciamento.set_focus()
    time.sleep(0.5)

    # Caminho para a pasta de OCR do módulo de credenciamento
    ocr_credenciamento = (lib_project_root / "src" / "lib_sisbr_desktop" / "ocr" / "plataforma_de_credenciamento").resolve()

    # Lista para armazenar os caminhos dos relatórios gerados
    caminhos_relatorios: list[str] = []

    # Caminhos das imagens (OCR) a serem utilizadas
    relatorios_img = ocr_credenciamento / "relatorios.png"
    liquidacao_slc_img = ocr_credenciamento / "liquidacao_slc.png"
    gerar_relatorio_img = ocr_credenciamento / "gerar_relatorio.png"
    imprimir_img = ocr_credenciamento / "imprimir.png"
    nenhum_item_img = ocr_credenciamento / "nenhum_item.png"
    ok_img = ocr_credenciamento / "ok.png"
    emitindo_relatorio_img = ocr_credenciamento / "emitindo_relatorio.png"
    try:
        # 1) Clicar em "Relatórios" e verificar que "Liquidação SLC" apareceu
        logger.info("Clicando em 'Relatórios' e verificando 'Liquidação SLC'...")
        click_and_verify(relatorios_img, liquidacao_slc_img)
        time.sleep(0.5)

        # Logo após, clicar na imagem "Liquidação SLC"
        logger.info("Clicando em 'Liquidação SLC'...")
        pos_liquidacao = get_position_img(liquidacao_slc_img)[1]
        pyautogui.click(pos_liquidacao)
        time.sleep(1.2)

        # 2) Preencher CPF/CNPJ usando coordenadas do mapeamento
        cpf_bounds = PLATAFORMA_DE_CREDENCIAMENTO["campo_cpf_cnpj"]["bounds"]
        cpf_l, cpf_t, cpf_r, cpf_b = cpf_bounds
        cpf_x = (cpf_l + cpf_r) // 2
        cpf_y = (cpf_t + cpf_b) // 2
        logger.info(f"Preenchendo CPF/CNPJ em ({cpf_x}, {cpf_y})...")
        write_with_retry_formatted(cpf_x, cpf_y, cpf_cnpj)
        

        # 3) Executar 3 vezes o preenchimento de datas, retrocedendo 30 dias por execução
        hoje = datetime.today()

        
        # Preparar coordenadas fixas dos campos de data a partir do mapeamento
        data1_bounds = PLATAFORMA_DE_CREDENCIAMENTO["campo_data_1"]["bounds"]
        data1_l, data1_t, data1_r, data1_b = data1_bounds
        data1_x = (data1_l + data1_r) // 2
        data1_y = (data1_t + data1_b) // 2

        data2_bounds = PLATAFORMA_DE_CREDENCIAMENTO["campo_data_2"]["bounds"]
        data2_l, data2_t, data2_r, data2_b = data2_bounds
        data2_x = (data2_l + data2_r) // 2
        data2_y = (data2_t + data2_b) // 2

        for i in range(3):
            # i = 0 -> [D-30, D]
            # i = 1 -> [D-60, D-30]
            # i = 2 -> [D-90, D-60]
            direita_dt = (hoje - timedelta(days=30 * i))
            esquerda_dt = (hoje - timedelta(days=30 * (i + 1)))
            data_esquerda_str = esquerda_dt.strftime("%d/%m/%Y")
            data_direita_str = direita_dt.strftime("%d/%m/%Y")

            logger.info(f"Execução {i+1}/3: DE ({data_esquerda_str}) | DD ({data_direita_str})")

            # Preencher Data Esquerda (campo Data 1)
            logger.info(f"Preenchendo Data 1 ({data1_x}, {data1_y}) com {data_esquerda_str}...")
            write_with_retry_formatted(data1_x, data1_y, data_esquerda_str)
            time.sleep(0.2)

            # Preencher Data Direita (campo Data 2)
            logger.info(f"Preenchendo Data 2 ({data2_x}, {data2_y}) com {data_direita_str}...")
            write_with_retry_formatted(data2_x, data2_y, data_direita_str)
            time.sleep(0.2)

            # 4) Gerar relatório e imprimir para cada execução
            logger.info("Clicando em 'Gerar Relatório' e verificando 'Imprimir'...")
            click_and_verify(gerar_relatorio_img, imprimir_img)
            time.sleep(0.6)

            logger.info("Clicando em 'Imprimir'...")
            pos_imprimir = get_position_img(imprimir_img)[1]
            pyautogui.click(pos_imprimir)
            time.sleep(0.8)
            
            # 5) Aguardar ciclo de emissão: esperar aparecer e depois desaparecer 'emitindo_relatorio'
            if emitindo_relatorio_img.exists():
                logger.info("Aguardando aparecer 'emitindo_relatorio' (até 10s)...")
                appeared = get_position_img(emitindo_relatorio_img, threshold=0.80, timeout=10, retry_delay=0.4)
                if appeared:
                    logger.info("'emitindo_relatorio' apareceu; aguardando desaparecer (até 120s)...")
                    t0 = time.time()
                    timeout_emitindo = 120
                    while time.time() - t0 < timeout_emitindo:
                        match_emitindo = get_position_img(emitindo_relatorio_img, threshold=0.80, timeout=2, retry_delay=0.4)
                        if not match_emitindo:
                            logger.info("'emitindo_relatorio' não está mais visível. Prosseguindo.")
                            break
                        time.sleep(0.3)
                    else:
                        logger.warning("Timeout ao aguardar desaparecer 'emitindo_relatorio'; prosseguindo mesmo assim.")
                else:
                    logger.info("'emitindo_relatorio' não apareceu no tempo esperado; prosseguindo.")
            else:
                logger.warning("Template 'emitindo_relatorio.png' não encontrado; pulando espera de emissão.")

            # 6) Após emissão: verificar 'nenhum_item' com uma única chamada (timeout 20s). Se não encontrado, gerenciar download
            logger.info("Verificando se há 'nenhum_item' na tela (timeout 20s)...")
            match_nenhum = get_position_img(nenhum_item_img, threshold=0.80, timeout=40, retry_delay=0.5)
            if match_nenhum:
                logger.info("Imagem 'nenhum_item' encontrada: sem itens para esta data. Pulando para a próxima data...")
                # Tentar clicar no botão 'OK' (timeout curto)
                match_ok = get_position_img(ok_img, threshold=0.80, timeout=5, retry_delay=0.5)
                if match_ok:
                    pyautogui.click(match_ok[1])
                    logger.info("Clique em 'OK' efetuado.")
                else:
                    logger.warning("Imagem 'ok' não encontrada no tempo esperado; prosseguindo mesmo assim.")
                continue

            # Gerenciar o download do arquivo PDF e somente prosseguir quando confirmado
            logger.info("Gerenciando o download do arquivo PDF...")
            # Ajuste: apontar para a pasta correta onde os relatórios estão sendo salvos
            pasta_download_temp = os.path.join(os.path.expanduser('~'), 'temp', 'credenciamento')
            caminho_final_relatorio = mover_relatorio_baixado(pasta_download_temp, pasta_destino_final, id_item)

            nome_final = f"LiquidacoesSLC_{id_item}_{cpf_cnpj}_{i}.pdf"
            novo_caminho = os.path.join(os.path.dirname(caminho_final_relatorio), nome_final)
            if os.path.exists(novo_caminho):
                os.remove(novo_caminho)
            os.rename(caminho_final_relatorio, novo_caminho)
            logger.info(f"Relatório renomeado para: {novo_caminho}")
            # Acumular o caminho do relatório gerado
            caminhos_relatorios.append(novo_caminho)
            
            fechar_leitor_pdf()

    
        logger.info("Fluxo de geração/impressão de 3 relatórios finalizado com sucesso.")

    except Exception as e:
        logger.error(f"Erro ao baixar SÚMULA DE CRÉDITO: {e}")
        try:
            error_handler(win_credenciamento)
        except Exception as eh:
            logger.warning(f"Falha ao executar error_handler: {eh}")
        raise
    
    time.sleep(0.8)
    return caminhos_relatorios

@retry(times=3, delay_s=2)
def baixar_docs_gerais_proposta(win_modulo, id_item: str, pasta_destino_final: str, produto: str, numero_proposta: str):
    logger.info("Iniciando download de documentos de crédito...")
    """
    Baixa os documentos da proposta do módulo de CRÉDITO usando o número da proposta.
    """
    logger.info("Garantindo que 'PLATAFORMA DE CRÉDITO' não esteja aberta previamente...")
    fechar_modulo(win_modulo, "PLATAFORMA DE CRÉDITO")
    logger.info("Acessando o módulo 'PLATAFORMA DE CRÉDITO'...")
    win_credito = acessar_modulo(win_modulo, "PLATAFORMA DE CRÉDITO", 5)
    if not win_credito:
        raise RuntimeError("Falha ao obter a janela do módulo 'PLATAFORMA DE CRÉDITO'.")
    time.sleep(3)

    logger.info(f"Acessando submódulo '{produto}'...")
    acessa_submodulo(win_credito, produto, plataforma="PLATAFORMA DE CRÉDITO")
    logger.info("Iniciando download dos documentos...")
    win_credito.set_focus()
    time.sleep(0.5)

    try:
        caminhos_relatorios: list[str] = []
        pasta_download_temp = os.path.join(os.path.expanduser('~'), 'AppData', 'Roaming', 'br.com.sicoob.sisbr.portalAir', 'Local Store')

        # Definições de imagens
        img_documentacao = ocr_credito / "documentacao.png"
        img_documentacao_ancora = ocr_credito / "documentacao_ancora.png"
        img_outros_documentacao_cinza = ocr_credito / "outros_documentacao_cinza_copia.png"
        img_outros_documentacao_claro = ocr_credito / "outros_documentacao_claro.png"
        img_ancora_download = ocr_credito / "ancora.png"
        img_ancora_download_1 = ocr_credito / "ancora_1.png"
        img_botao_baixar_relatorio = ocr_credito / "baixar_relatorio.png"
        img_botao_exit = ocr_credito / "exit.png"
        img_avaliacao_bem_cinza = ocr_credito / "comprovante_avaliacao_bem_cinza.png"
        img_avaliacao_bem_claro = ocr_credito / "comprovante_avaliacao_bem_claro.png"
        img_propriedade_veiculo_cinza = ocr_credito / "comprovante_propriedade_veiculo_cinza.png"
        img_propriedade_veiculo_claro = ocr_credito / "comprovante_propriedade_veiculo_claro.png"
        img_outros_garantia_cinza = ocr_credito / "outros_garantia_cinza.png"
        img_outros_garantia_claro = ocr_credito / "outros_garantia_claro.png"
        btn_operacoes_credito = ocr_credito / "operacoes_credito.png"
        btn_operacao_credito_consignado = ocr_credito / "operacao_credito_consignado.png"
        btn_operacao_credito_credito_rural = ocr_credito / "operacoes_credito_rural.png"
        bnt_antecipacao = ocr_credito / "antecipacao.png"
        bnt_recebiveis = ocr_credito / "recebiveis.png"
        btn_mesa_operacoes = ocr_credito / "mesa_operacoes.png"
        btn_verify = ocr_credito / "menu_mesa_de_operacoes.png"
        scroll_img = ocr_credito / "scroll.png"

        # Passo 1 - Acessar o módulo de Crédito
        logger.info("Acessando o módulo de Crédito...")

        if produto == "EMPRÉSTIMO":
            logger.info("Clicando em 'Operações de Crédito'...")
            click_and_verify(btn_operacoes_credito, btn_mesa_operacoes)

        elif produto == "CONCESSÃO DE LIMITES":
            logger.info("Clicando em 'ANTECIPAÇÃO'...")
            click_and_verify(bnt_antecipacao, bnt_recebiveis)
            logger.info("Clicando em 'RECEBÍVEIS'...")
            click_and_verify(bnt_recebiveis, btn_mesa_operacoes)

        elif produto == "CONSIGNADO":
            logger.info("Clicando em 'Operações de Crédito consignado'...")
            click_and_verify(btn_operacao_credito_consignado, btn_mesa_operacoes)

        elif produto == "CRÉDITO RURAL":
            logger.info("Clicando em 'Operações de Crédito rural'...")
            click_and_verify(btn_operacao_credito_credito_rural, btn_mesa_operacoes)

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
        time.sleep(3)  # Aguardar após clicar
        
        # Passo 1: Clicar em documentacao e verificar garantia_financiamento
        click_and_verify(img_documentacao, img_documentacao_ancora)

        # Definir configurações dos tipos de relatórios
        tipos_relatorios = [
            {
                "nome": "Outros Documentacao",
                "numero_tipo": 0,
                "img_cinza": img_outros_documentacao_cinza,
                "img_claro": img_outros_documentacao_claro,
                "usar_buscar_com_scroll": False,
                "usar_ancora_alternativa": True  # Usa ancora_1.png após o primeiro
            },
            {
                "nome": "Comprovante Avaliacao Bem",
                "numero_tipo": 1,
                "img_cinza": img_avaliacao_bem_cinza,
                "img_claro": img_avaliacao_bem_claro,
                "usar_buscar_com_scroll": True,
                "usar_ancora_alternativa": False  # Sempre usa ancora.png
            },
            {
                "nome": "Comprovante Propriedade Veiculo",
                "numero_tipo": 2,
                "img_cinza": img_propriedade_veiculo_cinza,
                "img_claro": img_propriedade_veiculo_claro,
                "usar_buscar_com_scroll": True,
                "usar_ancora_alternativa": True  # Usa ancora_1.png após o primeiro
            },
            {
                "nome": "Outros Garantia",
                "numero_tipo": 3,
                "img_cinza": img_outros_garantia_cinza,
                "img_claro": img_outros_garantia_claro,
                "usar_buscar_com_scroll": True,
                "usar_ancora_alternativa": True  # Usa ancora_1.png após o primeiro
            }
        ]

        # Passo 2-4: Processar todos os tipos de relatórios em um único loop
        logger.info(f"Iniciando processamento de {len(tipos_relatorios)} tipos de relatórios...")
        for idx, tipo_relatorio in enumerate(tipos_relatorios, 1):
            nome = tipo_relatorio["nome"]
            numero_tipo = tipo_relatorio["numero_tipo"]
            img_cinza = tipo_relatorio["img_cinza"]
            img_claro = tipo_relatorio["img_claro"]
            usar_buscar_com_scroll = tipo_relatorio["usar_buscar_com_scroll"]
            usar_ancora_alternativa = tipo_relatorio["usar_ancora_alternativa"]
            
            logger.info(f"[{idx}/{len(tipos_relatorios)}] Processando {nome} (tipo {numero_tipo})...")
            logger.debug(f"Configurações: buscar_com_scroll={usar_buscar_com_scroll}, ancora_alternativa={usar_ancora_alternativa}")
            
            # Buscar a imagem do relatório
            regiao_outros = PLATAFORMA_DE_CREDITO["regiao_outros_documentacao"]["bounds"]
            logger.debug(f"Região de busca: {regiao_outros}")
            
            if usar_buscar_com_scroll:
                logger.info(f"Buscando {nome} com scroll...")
                relatorio_pos = buscar_com_scroll(img_cinza, img_claro, screenshot_region=regiao_outros)
            else:
                logger.info(f"Buscando {nome} sem scroll (imagem cinza primeiro)...")
                relatorio_pos = get_position_img(img_cinza, timeout=6, threshold=0.85, screenshot_region=regiao_outros)
                if not relatorio_pos:
                    logger.info(f"Imagem cinza não encontrada, tentando imagem clara...")
                    relatorio_pos = get_position_img(img_claro, timeout=6, threshold=0.85, screenshot_region=regiao_outros)
            
            if not relatorio_pos:
                logger.warning(f"{nome} não encontrado para {id_item}, prosseguindo para o próximo tipo de relatório.")
                continue
            
            logger.success(f"{nome} encontrado na posição {relatorio_pos[1]}")
            
            # Clicar no relatório encontrado
            logger.info(f"Clicando em {nome}...")
            pyautogui.click(relatorio_pos[1])
            regiao_ancora = PLATAFORMA_DE_CREDITO["regiao_ancora_download"]["bounds"]
            logger.debug(f"Região da âncora: {regiao_ancora}")
            time.sleep(2)
            logger.info("Aguardando carregamento da tabela de relatórios...")
            get_position_img_ordered(img_ancora_download, timeout=6, screenshot_region=regiao_ancora, threshold=0.95)
            
            # Processar múltiplos relatórios na tabela
            relatorio_count = 0
            logger.info(f"Iniciando busca por relatórios individuais de {nome}...")
            while True:
                logger.debug(f"Tentativa {relatorio_count + 1} - Localizando âncora...")
                
                # Localizar a âncora
                if usar_ancora_alternativa and relatorio_count > 0:
                    logger.debug("Usando âncora alternativa (ancora_1.png)")
                    ancora_pos = get_position_img_ordered(img_ancora_download_1, screenshot_region=regiao_ancora, timeout=6, threshold=0.95)
                else:
                    logger.debug("Usando âncora padrão (ancora.png)")
                    ancora_pos = get_position_img_ordered(img_ancora_download, screenshot_region=regiao_ancora, timeout=6, threshold=0.95)
                
                if not ancora_pos:
                    logger.info(f"Âncora não encontrada após {relatorio_count} relatórios. Finalizando busca para {nome}.")
                    break
                
                logger.info(f"Âncora encontrada, clicando para baixar relatório {relatorio_count + 1}...")
                
                pyautogui.click(ancora_pos[1])
                
                # Verificar se aparece a imagem baixar_relatorio e clicar nela
                logger.debug("Aguardando botão de download aparecer...")
                time.sleep(3)
                baixar_pos = get_position_img(img_botao_baixar_relatorio, threshold=0.85, timeout=4)
                if baixar_pos:
                    logger.info("Botão 'Baixar Relatório' encontrado, iniciando download...")
                    pyautogui.click(baixar_pos[1])
                    time.sleep(0.5)
                else:
                    logger.warning("Botão 'Baixar Relatório' não encontrado, continuando...")
                
                # Gerenciar download
                logger.info("Movendo arquivo baixado para pasta de destino...")
                caminho_final = mover_relatorio_baixado(pasta_download_temp, pasta_destino_final, id_item)
                nome_final = f"DocsGeraisProposta_{numero_tipo}_{relatorio_count}_id_item_{id_item}.pdf"
                novo_caminho = os.path.join(os.path.dirname(caminho_final), nome_final)
                
                if os.path.exists(novo_caminho):
                    logger.warning(f"Arquivo {nome_final} já existe, removendo versão anterior...")
                    os.remove(novo_caminho)
                
                os.rename(caminho_final, novo_caminho)
                logger.success(f"Arquivo renomeado para: {nome_final}")
                caminhos_relatorios.append(novo_caminho)
                
                logger.info("Fechando leitor PDF...")
                fechar_leitor_pdf()
                
                # Verificar se existe a imagem 'exit' na região especificada
                regiao_exit = PLATAFORMA_DE_CREDITO["regiao_exit_button"]["bounds"]
                logger.debug(f"Verificando pop-up de exit na região: {regiao_exit}")

                # Fechando pop-up caso apareça
                exit_pos = get_position_img(img_botao_exit, screenshot_region=regiao_exit, threshold=0.85, timeout=6)
                if exit_pos:
                    pyautogui.click(exit_pos[1])
                    logger.info("Pop-up 'exit' encontrado e fechado.")
                    time.sleep(0.5)
                else:
                    logger.debug("Nenhum pop-up 'exit' encontrado.")
                
                relatorio_count += 1
                logger.success(f"✓ Relatório {relatorio_count} de {nome} baixado com sucesso!")
                
                # Verificar se há mais relatórios navegando com tecla down
                logger.debug("Verificando se há mais relatórios disponíveis...")
                regiao_mudanca_cor = PLATAFORMA_DE_CREDITO["regiao_mudanca_cor_dinamica"]["bounds"]
                if not verificar_mudanca_cor_dinamica(region=regiao_mudanca_cor):
                    logger.info(f"Não há mais relatórios de {nome} disponíveis na tabela.")
                    break
                else:
                    logger.info("Mais relatórios encontrados, continuando...")
            
            # Reset scroll após download se necessário
            if usar_buscar_com_scroll:
                logger.info("Resetando scroll para próximo tipo de relatório...")
                scroll_pos = get_position_img(scroll_img, timeout=6, threshold=0.95)
                if scroll_pos:
                    pyautogui.moveTo(scroll_pos[1])
                    pyautogui.scroll(10000)
                    logger.debug("Scroll resetado com sucesso.")
                else:
                    logger.warning("Imagem de scroll não encontrada para reset.")
            
            # Fazer hover na imagem documentacao_ancora no final do loop
            logger.debug("Fazendo hover na âncora de documentação...")
            documentacao_ancora_pos = get_position_img(img_documentacao_ancora, timeout=2)
            if documentacao_ancora_pos:
                pyautogui.moveTo(documentacao_ancora_pos[1])
                time.sleep(0.5)
                logger.debug("Hover realizado com sucesso.")
            else:
                logger.warning("Âncora de documentação não encontrada para hover.")
            
            logger.success(f"✓ Processamento de {nome} concluído! Total de relatórios baixados: {relatorio_count}")

        # Resumo final do processamento
        total_relatorios = len(caminhos_relatorios)
        logger.success(f"🎉 Fluxo de geração/impressão de relatórios finalizado com sucesso!")
        logger.info(f"📊 Resumo: {total_relatorios} relatórios baixados de {len(tipos_relatorios)} tipos processados")
        
        for i, caminho in enumerate(caminhos_relatorios, 1):
            nome_arquivo = os.path.basename(caminho)
            logger.info(f"  {i}. {nome_arquivo}")
        
        return caminhos_relatorios
            

    except Exception as e:
        logger.error(f"Erro ao baixar SÚMULA DE CRÉDITO: {e}")
        try:
            error_handler(win_credito)
        except Exception as eh:
            logger.warning(f"Falha ao executar error_handler: {eh}")
        raise

@retry(times=3, delay_s=2)
def baixar_documentos_garantia(win_modulo, id_item: str, pasta_destino_final: str, produto: str, numero_proposta: str):
    logger.info("Iniciando download de garantias...")

    """
    Baixa os relatórios das garantias do módulo de CRÉDITO usando o número da proposta.
    """
    logger.info("Garantindo que 'PLATAFORMA DE CRÉDITO' não esteja aberta previamente...")
    fechar_modulo(win_modulo, "PLATAFORMA DE CRÉDITO")
    logger.info("Acessando o módulo 'PLATAFORMA DE CRÉDITO'...")
    win_credito = acessar_modulo(win_modulo, "PLATAFORMA DE CRÉDITO", 5)
    if not win_credito:
        raise RuntimeError("Falha ao obter a janela do módulo 'PLATAFORMA DE CRÉDITO'.")
    time.sleep(3)

    logger.info(f"Acessando submódulo '{produto}'...")
    acessa_submodulo(win_credito, produto, plataforma="PLATAFORMA DE CRÉDITO")
    logger.info("Iniciando download das garantias...")
    win_credito.set_focus()
    time.sleep(0.5)

    try:
        caminhos_relatorios: list[str] = []

        # Definições de imagens
        img_botao_exit = ocr_credito / "exit.png"
        img_garantia = ocr_credito / "garantia.png"
        img_garantia_ancora = ocr_credito / "garantia_ancora.png"
        img_visualizar = ocr_credito / "visualizar.png"
        img_visualizar_garantia = ocr_credito / "visualizar_garantia.png"
        btn_operacoes_credito = ocr_credito / "operacoes_credito.png"
        btn_operacao_credito_consignado = ocr_credito / "operacao_credito_consignado.png"
        btn_operacao_credito_credito_rural = ocr_credito / "operacoes_credito_rural.png"
        bnt_antecipacao = ocr_credito / "antecipacao.png"
        bnt_recebiveis = ocr_credito / "recebiveis.png"
        btn_mesa_operacoes = ocr_credito / "mesa_operacoes.png"
        btn_verify = ocr_credito / "menu_mesa_de_operacoes.png"

        # Passo 1 - Acessar o módulo de Crédito
        logger.info("Acessando o módulo de Crédito...")

        if produto == "EMPRÉSTIMO":
            logger.info("Clicando em 'Operações de Crédito'...")
            click_and_verify(btn_operacoes_credito, btn_mesa_operacoes)

        elif produto == "CONCESSÃO DE LIMITES":
            logger.info("Clicando em 'ANTECIPAÇÃO'...")
            click_and_verify(bnt_antecipacao, bnt_recebiveis)
            logger.info("Clicando em 'RECEBÍVEIS'...")
            click_and_verify(bnt_recebiveis, btn_mesa_operacoes)

        elif produto == "CONSIGNADO":
            logger.info("Clicando em 'Operações de Crédito consignado'...")
            click_and_verify(btn_operacao_credito_consignado, btn_mesa_operacoes)

        elif produto == "CRÉDITO RURAL":
            logger.info("Clicando em 'Operações de Crédito rural'...")
            click_and_verify(btn_operacao_credito_credito_rural, btn_mesa_operacoes)

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
        time.sleep(3)  # Aguardar após clicar
        
        # Passo 8 - Processar relatório de garantias
        logger.info("Iniciando processamento do relatório de garantias...")
        
        # Clicar na imagem garantia e verificar garantia_ancora
        logger.info("Clicando em 'Garantia'...")
        click_and_verify(img_garantia, img_garantia_ancora)
        time.sleep(7)
        
        # Obter coordenadas dos itens de garantia do mapeamento
        COORDENADAS_GARANTIAS = PLATAFORMA_DE_CREDITO["coordenadas_garantias"]

        # Obter coordenadas para captura de screenshot do mapeamento
        screenshot_bounds = PLATAFORMA_DE_CREDITO["coordenadas_screenshot_garantias"]["bounds"]
        screenshot_x1, screenshot_y1, screenshot_x2, screenshot_y2 = screenshot_bounds
        
        garantia_count = 0
        
        # Loop através das coordenadas predefinidas (similar ao plataforma_atendimento.py)
        logger.info("Verificando se os campos mudam de cor ao clicar...")
        for idx, coord in enumerate(COORDENADAS_GARANTIAS):
            # Calcula as coordenadas do centro do retângulo definido por 'coord'
            x = (coord['l'] + coord['r']) // 2
            y = (coord['t'] + coord['b']) // 2
            
            logger.info(f"Verificando item de garantia {idx + 1}...")
            
            if verificar_campo_muda_de_cor(coord):
                logger.info(f"Item {idx + 1} centro (x={x}, y={y}) é CLICÁVEL (mudou de cor ao clicar). Processando garantia...")
                
                logger.info(f"Garantia encontrada no item {idx + 1}. Processando...")
                
                # Clicar na imagem "visualizar" e verificar "visualizar_garantia"
                logger.info("Clicando em 'Visualizar'...")
                click_and_verify(img_visualizar, img_visualizar_garantia)
                
                # Aguardar 10 segundos
                time.sleep(10)
                
                # Capturar screenshot da área especificada
                logger.info("Capturando screenshot da garantia...")
                screenshot = pyautogui.screenshot(region=(
                    screenshot_x1, screenshot_y1,
                    screenshot_x2 - screenshot_x1, screenshot_y2 - screenshot_y1
                ))
                
                # Salvar o screenshot na pasta temp/relatorios_finais
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                nome_arquivo = f"Garantias_{garantia_count}_{id_item}_{numero_proposta}_.png"
                caminho_screenshot = os.path.join(pasta_destino_final, nome_arquivo)
                
                # Criar diretório se não existir
                os.makedirs(pasta_destino_final, exist_ok=True)
                screenshot.save(caminho_screenshot)
                
                logger.success(f"Screenshot da garantia salvo em: {caminho_screenshot}")
                caminhos_relatorios.append(caminho_screenshot)
                garantia_count += 1
                
                # Clicar na imagem "exit" e verificar "visualizar"
                logger.info("Fechando visualização da garantia...")
                click_and_verify(img_botao_exit, img_visualizar)
            else:
                logger.warning(f"Retângulo {idx+1} centro (x={x}, y={y}) NÃO mudou de cor ao clicar. Fim da lista de contas.")
                break
            time.sleep(0.3)

        
        logger.success(f"Processamento de garantias concluído. Total de garantias processadas: {garantia_count}")
        return caminhos_relatorios

    except Exception as e:
        logger.error(f"Erro ao baixar SÚMULA DE CRÉDITO: {e}")
        try:
            error_handler(win_credito)
        except Exception as eh:
            logger.warning(f"Falha ao executar error_handler: {eh}")
        raise
