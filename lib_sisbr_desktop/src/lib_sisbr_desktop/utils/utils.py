import cv2
import numpy as np
import pyautogui
from loguru import logger
from pathlib import Path
from pywinauto import Application, findwindows
import psutil
import time
import os
import shutil
import requests

# Desabilita o fail-safe do PyAutoGUI para evitar interrupções
pyautogui.FAILSAFE = False

def get_variable(value):
    if value is None:
        return ""
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, (list, tuple)):
        return " ".join(str(v) for v in value if v is not None)
    if isinstance(value, dict):
        for k in ("cpf_cnpj_avalista", "data", "value", "texto"):
            if k in value and value[k]:
                return str(value[k])
        return " ".join(str(v) for v in value.values() if v is not None)
    s = str(value).strip()
    # Remove aspas de início/fim, se presentes (ex.: "035.734.951-25")
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        s = s[1:-1]
    return s 

def encontrar_relatorios_na_tela(template_path, threshold=0.85, roi=None):
    template = cv2.imread(str(template_path), cv2.IMREAD_COLOR)
    if template is None:
        logger.error(f"Template do relatório não encontrado: {template_path}")
        return []
    h, w, _ = template.shape
    screenshot = pyautogui.screenshot()
    screenshot_np = np.array(screenshot)
    screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
    # Se ROI for fornecido, recorta a imagem
    if roi:
        l, t, w_roi, h_roi = roi['l'], roi['t'], roi['w'], roi['h']
        screenshot_bgr_roi = screenshot_bgr[t:t+h_roi, l:l+w_roi]
    else:
        screenshot_bgr_roi = screenshot_bgr
    result = cv2.matchTemplate(screenshot_bgr_roi, template, cv2.TM_CCOEFF_NORMED)
    loc = np.where(result >= threshold)
    pontos = list(zip(*loc[::-1]))
    pontos_filtrados = []
    for pt in pontos:
        # Ajusta as coordenadas para a tela inteira se usou ROI
        if roi:
            pt = (pt[0] + l, pt[1] + t)
        if not any(np.linalg.norm(np.array(pt) - np.array(pf)) < min(h, w)//2 for pf in pontos_filtrados):
            pontos_filtrados.append(pt)
    return pontos_filtrados

def logar_relatorios_encontrados(pontos_relatorio):
    logger.info(f"Foram encontrados {len(pontos_relatorio)} relatórios na tela.")
    for idx, pt in enumerate(pontos_relatorio):
        logger.info(f"Relatório {idx+1}: posição (x={pt[0]}, y={pt[1]})")

def fechar_janela_ged(titulo="Visualização de documentos GED", timeout=10):
    try:
        start = time.time()
        while time.time() - start < timeout:
            try:
                # Busca por janelas com o título (sem amarrar a um PID específico)
                handles = findwindows.find_windows(title_re=f".*{titulo}.*")
            except Exception:
                handles = []

            if handles:
                for handle in handles:
                    try:
                        # Conecta-se diretamente pelo handle e fecha a janela
                        app = Application(backend="win32").connect(handle=handle)
                        janela = app.window(handle=handle)
                        try:
                            janela.close()
                            logger.info(f"Janela '{titulo}' fechada com sucesso.")
                        except Exception:
                            # Fallback: tentar Alt+F4 via pyautogui se necessário
                            try:
                                pyautogui.hotkey('alt', 'f4')
                                logger.info(f"Tentado fechar '{titulo}' com Alt+F4.")
                            except Exception:
                                pass
                    except Exception:
                        continue
                return

            time.sleep(0.5)
        logger.warning(f"Janela '{titulo}' não encontrada para fechar.")
    except Exception as e:
        logger.warning(f"Não foi possível fechar a janela '{titulo}': {e}")

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


def limpar_restauracao_edge():
    """
    Mitiga o banner de restauração do Microsoft Edge sem encerrar processos:
    remove arquivos de sessão/tabs e marca saída limpa nos arquivos de preferências.
    """
    try:
        # NÃO encerra o Edge; apenas tenta limpar vestígios quando possível
        base_user = os.path.join(os.getenv('LOCALAPPDATA', ''), 'Microsoft', 'Edge', 'User Data')
        default_profile = os.path.join(base_user, 'Default')
        if not default_profile or not os.path.isdir(default_profile):
            logger.info("Perfil Default do Edge não encontrado; pulando limpeza de sessão.")
            return

        # 1) Remover arquivos típicos de sessão/abas que acionam restauração
        padroes = [
            'Last Session', 'Last Tabs', 'Current Session', 'Current Tabs',
            'Session Storage', 'Sessions', 'Restore Last Session'
        ]
        removidos = 0
        try:
            for nome in os.listdir(default_profile):
                for padrao in padroes:
                    if padrao.lower() in nome.lower():
                        caminho = os.path.join(default_profile, nome)
                        try:
                            if os.path.isdir(caminho):
                                shutil.rmtree(caminho, ignore_errors=True)
                            else:
                                os.remove(caminho)
                            removidos += 1
                        except Exception:
                            # pode estar em uso; ignore
                            pass
        except Exception:
            pass

        # 2) Marcar saída limpa nos JSONs de preferências (best-effort)
        import json
        pref_path = os.path.join(default_profile, 'Preferences')
        local_state_path = os.path.join(base_user, 'Local State')

        def _ajustar_json_flag(caminho, edits):
            try:
                if not os.path.isfile(caminho):
                    return False
                with open(caminho, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                # aplica edições simples
                for key, value in edits.items():
                    data[key] = value
                with open(caminho, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False)
                return True
            except Exception:
                return False

        ok_pref = _ajustar_json_flag(pref_path, {"exit_type": "None", "exited_cleanly": True})
        ok_local = _ajustar_json_flag(local_state_path, {"exited_cleanly": True})

        logger.info(f"Limpeza Edge: removidos={removidos}, pref_ok={ok_pref}, local_ok={ok_local}")
    except Exception as e:
        logger.warning(f"Falha ao limpar restauração do Edge: {e}")

def fechar_todas_instancias_sisbr():
    for proc in psutil.process_iter(['pid', 'name']):
        if 'sisbr' in proc.info['name'].lower():
            try:
                proc.kill()
                logger.info(f"Processo Sisbr (PID: {proc.info['pid']}) encerrado.")
            except Exception as e:
                logger.warning(f"Erro ao encerrar processo Sisbr: {e}")

from lib_sisbr_desktop.src.lib_sisbr_desktop.gui.helpers import get_position_img
import os
import time
from pathlib import Path
from loguru import logger


def aguardar_arquivo_baixado(pasta_download, extensao="*.pdf", tempo_limite=30, tempo_estabilidade=3, timeout=30):
    """
    Aguarda o download de um arquivo na pasta especificada.
    
    A função procura por arquivos que foram modificados/criados nos últimos 'tempo_limite' segundos.
    Se não encontrar nenhum arquivo dentro do tempo total especificado, levanta uma exceção.
    
    Args:
        pasta_download (str): Caminho da pasta onde o arquivo será baixado
        extensao (str): Extensão dos arquivos a serem verificados (padrão: "*.pdf")
        tempo_limite (int): Tempo máximo em segundos para considerar um arquivo como recente (padrão: 30)
        tempo_estabilidade (int): Tempo mínimo em segundos que o arquivo deve permanecer inalterado (padrão: 3)
        timeout (int): Tempo máximo total de espera em segundos (padrão: 30)
        
    Returns:
        Path: Caminho do arquivo baixado
        
    Raises:
        TimeoutError: Se nenhum arquivo for encontrado dentro do tempo limite
    """
    tempo_inicio = time.time()
    tempo_final = tempo_inicio + timeout
    
    logger.info(f"Aguardando download do arquivo {extensao} na pasta {pasta_download}...")
    logger.info(f"Procurando por arquivos modificados nos últimos {tempo_limite} segundos...")
    
    while time.time() < tempo_final:
        try:
            # Lista todos os arquivos com a extensão especificada
            arquivos = list(Path(pasta_download).rglob(extensao))
            agora = time.time()
            
            if arquivos:
                # Pega o arquivo mais recente
                arquivo_mais_recente = max(
                    arquivos,
                    key=lambda f: max(os.path.getmtime(f), os.path.getctime(f))
                )
                
                # Calcula o tempo desde a última modificação
                tempo_desde_modificacao = agora - max(
                    os.path.getmtime(arquivo_mais_recente),
                    os.path.getctime(arquivo_mais_recente)
                )
                
                logger.info(f"Arquivo encontrado: {arquivo_mais_recente} (modificado há {tempo_desde_modificacao:.1f}s)")
                
                # Verifica se o arquivo está dentro do tempo limite
                if tempo_desde_modificacao <= tempo_limite:
                    # Verifica se o arquivo está estável
                    if tempo_desde_modificacao > tempo_estabilidade:
                        logger.success(f"Arquivo baixado e estável: {arquivo_mais_recente}")
                        return arquivo_mais_recente
                    else:
                        logger.debug(f"Aguardando estabilização do arquivo: {tempo_estabilidade - tempo_desde_modificacao:.1f}s restantes")
                else:
                    logger.warning(f"Arquivo encontrado, mas fora do tempo limite de {tempo_limite}s")
            
            # Mostra o tempo restante a cada 5 segundos
            tempo_restante = tempo_final - time.time()
            if tempo_restante > 0 and int(tempo_restante) % 5 == 0:
                logger.info(f"Aguardando arquivo... (mais {int(tempo_restante)}s restantes)")
                
            time.sleep(1)
            
        except Exception as e:
            logger.warning(f"Erro ao verificar arquivos baixados: {e}")
            time.sleep(1)
    
    # Se chegou aqui, o tempo total de espera foi esgotado
    mensagem_erro = f"Timeout: Nenhum arquivo {extensao} modificado nos últimos {tempo_limite}s foi encontrado na pasta {pasta_download} após {timeout} segundos."
    logger.error(mensagem_erro)
    raise TimeoutError(mensagem_erro)


def fechar_popup_ia(ocr_path):
    """
    Fecha o pop-up da IA que aparece quando a plataforma de atendimento é aberta.
    Clica diretamente nas coordenadas fornecidas.
    """
    logger.info("Verificando e fechando pop-up da IA...")

    try:
        time.sleep(1)
        ia_img = ocr_path / "ia.png"
        fechar_img = ocr_path / "fechar_ia.png"

        # Hover na imagem da IA
        result_ia = get_position_img(ia_img, threshold=0.8, timeout=5)
        if result_ia:
            _, (x_ia, y_ia) = result_ia
            logger.info(f"Hover na IA em ({x_ia}, {y_ia})")
            pyautogui.moveTo(x_ia, y_ia)
            time.sleep(0.8)
        else:
            logger.info("Imagem 'ia.png' não encontrada (seguindo mesmo assim)...")

        # Clique no centro do botão fechar da IA
        result_close = get_position_img(fechar_img, threshold=0.8, timeout=5)
        if result_close:
            _, (x_close, y_close) = result_close
            logger.info(f"Clicando em fechar IA em ({x_close}, {y_close})")
            pyautogui.moveTo(x_close, y_close)
            pyautogui.click()
            logger.success("Pop-up da IA fechado com sucesso")
        else:
            logger.info("Imagem 'fechar_ia.png' não encontrada. Nada a fechar.")

        time.sleep(0.5)
    except Exception:
        logger.info("Erro ao fechar pop-up da IA - pode não estar presente")

def update_item_db(item_id, status=None, json_data=None):
    DATABASE_URL = "http://10.10.201.10:3000"
    DATABASE_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoidXN1YXJpb193ZWIiLCJ1c2VyX2lkIjoxMjMsImV4cCI6MjAwMDAwMDAwMH0.7Rj-5ioZPW0-gzI1qDUG6WRuP3YpWPVJWaARaIVM7gk"

    url = DATABASE_URL.rstrip("/") + f"/items?item_id=eq.{item_id}"
    headers = {
        "apikey": DATABASE_API_KEY,
        "Authorization": f"Bearer {DATABASE_API_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
 
    current = requests.get(url, headers=headers)
    current.raise_for_status()
    items = current.json() if current.text else []
    current_data = items[0].get("data", {}) if items else {}
 
    if json_data:
        if not isinstance(current_data, dict):
            current_data = {}
        if isinstance(json_data, dict):
            current_data.update(json_data)

    payload = {}
    if status:
        payload["status"] = status
    if current_data:
        payload["data"] = current_data

    resp = requests.patch(url, headers=headers, json=payload)
    resp.raise_for_status()
    return resp.json()

def add_etapa_finalizada(item_id, nome_relatorio):
    DATABASE_URL = "http://10.10.201.10:3000"
    DATABASE_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoidXN1YXJpb193ZWIiLCJ1c2VyX2lkIjoxMjMsImV4cCI6MjAwMDAwMDAwMH0.7Rj-5ioZPW0-gzI1qDUG6WRuP3YpWPVJWaARaIVM7gk"

    url = DATABASE_URL.rstrip("/") + f"/items?item_id=eq.{item_id}"
    headers = {
        "apikey": DATABASE_API_KEY,
        "Authorization": f"Bearer {DATABASE_API_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    resp_get = requests.get(url, headers=headers)
    resp_get.raise_for_status()
    items = resp_get.json() if resp_get.text else []
    data = items[0].get("data", {}) if items else {}

    etapas = []
    if isinstance(data, dict):
        ef = data.get("etapas_finalizadas")
        if isinstance(ef, list):
            etapas = ef.copy()

    if nome_relatorio and nome_relatorio not in etapas:
        etapas.append(nome_relatorio)

    if not isinstance(data, dict):
        data = {}
    data["etapas_finalizadas"] = etapas

    payload = {"data": data}
    resp_patch = requests.patch(url, headers=headers, json=payload)
    resp_patch.raise_for_status()
    return resp_patch.json()