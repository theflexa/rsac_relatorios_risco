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
ocr_painel_comercial = (lib_project_root / "src" / "lib_sisbr_desktop" / "ocr" / "painel_comercial").resolve()


@retry(times=3, delay_s=2)
def baixar_relatorio_painel_comercial(win_modulo, id_item: str, pasta_destino_final: str, cpf_cnpj):
    """
    Baixa os relatórios AnaliseConsolidada e FichaDetalhada do módulo PAINEL COMERCIAL.
    """
    logger.info("Iniciando download dos relatórios do PAINEL COMERCIAL...")
    win_modulo.set_focus()
    
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
            
            # Clicar no centro do retângulo onde aparece o nome do usuário
            coord_nome_usuario = {'l': 104, 't': 251, 'w': 1816, 'h': 733}
            x_centro_nome = coord_nome_usuario['l'] + coord_nome_usuario['w'] // 2
            y_centro_nome = coord_nome_usuario['t'] + coord_nome_usuario['h'] // 2
            
            logger.info(f"Clicando no centro do retângulo do nome do usuário em ({x_centro_nome}, {y_centro_nome})")
            pyautogui.moveTo(x_centro_nome, y_centro_nome)
            pyautogui.click()
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
                # Procurar por arquivos PDF recentes na pasta Downloads
                pdf_files = list(downloads_path.glob("*.pdf"))
                if pdf_files:
                    # Pegar o arquivo mais recente
                    latest_file = max(pdf_files, key=lambda f: f.stat().st_mtime)
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
                # Procurar por arquivos PDF recentes na pasta Downloads
                pdf_files = list(downloads_path.glob("*.pdf"))
                if pdf_files:
                    # Pegar o arquivo mais recente
                    latest_file = max(pdf_files, key=lambda f: f.stat().st_mtime)
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
            
            return relatorios_baixados
        
    except Exception as e:
        logger.error(f"Erro ao baixar relatórios do PAINEL COMERCIAL: {e}")
        raise


class DummyWin:
    def set_focus(self):
        pass


if __name__ == "__main__":
    win_modulo = DummyWin()
    id_item = "123"
    cpf_cnpj = "70852015178"  # CPF de teste
    PASTA_RELATORIOS_FINAL = str(project_root / "temp/relatorios_finais")
    
    logger.info("Iniciando teste de download dos relatórios do PAINEL COMERCIAL...")
    caminhos_relatorios = baixar_relatorio_painel_comercial(win_modulo, id_item, PASTA_RELATORIOS_FINAL, cpf_cnpj)
    logger.info(f"Caminhos dos relatórios salvos: {caminhos_relatorios}") 