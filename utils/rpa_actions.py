"""
================================================================================
RPA ACTIONS - Biblioteca de Funções RPA Estilo UiPath
================================================================================
Funções de automação inspiradas no UiPath para uso com Selenium.

Funções disponíveis:
- click()            - Clique com retry e verify
- type_into()        - Digitação com verify de texto
- select_item()      - Seleção em dropdowns
- wait_element()     - Aguardar elementos
- kill_process()     - Encerra um processo pelo nome
- kill_all_processes()- Encerra todos os processos configurados

Exemplo de uso:
    from utils.rpa_actions import click, type_into, kill_process, kill_all_processes
    
    # Encerrar processos antes de iniciar automação
    kill_all_processes()  # Lê do config/processes_to_kill.json
    kill_process("chrome.exe")
    
    click(driver, "//button[@id='submit']", verify_selector="//div[@class='success']", retry_count=3)
    type_into(driver, "//input[@id='email']", "teste@email.com", verify_text=True)
================================================================================
"""

import time
import subprocess
import json
from pathlib import Path
from typing import Optional, List, Dict

try:
    from loguru import logger
except ImportError:  # pragma: no cover - fallback para ambiente sem loguru instalado
    import logging

    logger = logging.getLogger(__name__)

try:
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.support.ui import WebDriverWait, Select
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import (
        TimeoutException,
        NoSuchElementException,
        ElementClickInterceptedException,
    )
    SELENIUM_AVAILABLE = True
except ImportError:  # pragma: no cover - fallback para ambiente sem selenium instalado
    SELENIUM_AVAILABLE = False

    class By:  # noqa: N801
        XPATH = "xpath"
        CSS_SELECTOR = "css selector"
        ID = "id"
        NAME = "name"

    class TimeoutException(Exception):
        pass

    class NoSuchElementException(Exception):
        pass

    class ElementClickInterceptedException(Exception):
        pass

    class _MissingSelenium:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("selenium não está instalado para usar utils/rpa_actions.py")

    ActionChains = _MissingSelenium
    WebDriverWait = _MissingSelenium
    Select = _MissingSelenium

    class _ExpectedConditionsProxy:
        def __getattr__(self, name):
            raise RuntimeError("selenium não está instalado para usar utils/rpa_actions.py")

    EC = _ExpectedConditionsProxy()


# ==============================================================================
# FUNÇÃO: click()
# ==============================================================================

def click(
    driver,
    selector: str,
    selector_type=By.XPATH,
    click_type: str = "single",
    mouse_button: str = "left",
    delay_before: float = 0.2,
    delay_after: float = 0.3,
    timeout: int = 10,
    continue_on_error: bool = False,
    verify_selector: str = None,
    verify_type=By.XPATH,
    verify_timeout: int = 5,
    retry_count: int = 0,
    retry_delay: float = 1.0
) -> bool:
    """
    Clica em um elemento com opções avançadas estilo UiPath.
    
    Args:
        driver: Instância do WebDriver
        selector: Seletor do elemento
        selector_type: Tipo do seletor (By.XPATH, By.CSS_SELECTOR, etc.)
        click_type: "single" ou "double"
        mouse_button: "left", "right" ou "middle"
        delay_before: Delay antes do clique (segundos)
        delay_after: Delay após o clique (segundos)
        timeout: Tempo máximo para encontrar elemento
        continue_on_error: Se True, não lança exceção em caso de erro
        verify_selector: Seletor do elemento para verificar após clique
        verify_type: Tipo do verify_selector
        verify_timeout: Timeout para verificação
        retry_count: Número de tentativas se verify falhar
        retry_delay: Delay entre tentativas
        
    Returns:
        bool: True se sucesso, False se falha
    """
    attempt = 0
    max_attempts = retry_count + 1
    
    while attempt < max_attempts:
        try:
            attempt += 1
            
            # Delay antes
            if delay_before > 0:
                time.sleep(delay_before)
            
            # Encontra elemento
            logger.trace(f"[Click] Procurando elemento: {selector[:60]}...")
            wait = WebDriverWait(driver, timeout)
            elemento = wait.until(EC.element_to_be_clickable((selector_type, selector)))
            
            # Executa clique baseado no tipo e botão
            actions = ActionChains(driver)
            
            if mouse_button == "left":
                if click_type == "double":
                    actions.double_click(elemento).perform()
                    logger.trace("[Click] Clique duplo executado")
                else:
                    elemento.click()
                    logger.trace("[Click] Clique simples executado")
            elif mouse_button == "right":
                actions.context_click(elemento).perform()
                logger.trace("[Click] Clique com botão direito executado")
            elif mouse_button == "middle":
                actions.click(elemento).perform()
                logger.trace("[Click] Clique com botão do meio executado")
            
            # Delay após
            if delay_after > 0:
                time.sleep(delay_after)
            
            # Verificação (se definida)
            if verify_selector:
                logger.trace(f"[Click] Validando: {verify_selector[:50]}...")
                try:
                    WebDriverWait(driver, verify_timeout).until(
                        EC.visibility_of_element_located((verify_type, verify_selector))
                    )
                    logger.success("[Click] Validação concluída com sucesso.")
                    return True
                except TimeoutException:
                    if attempt < max_attempts:
                        logger.warning(f"[Click] Validação falhou. Tentativa {attempt}/{max_attempts}. Retentando em {retry_delay}s...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        logger.error(f"[Click] Validação falhou após {max_attempts} tentativas")
                        if continue_on_error:
                            return False
                        raise TimeoutException(f"Validação falhou para: {verify_selector}")
            logger.success(f"[Click] Sucesso.")
            return True
            
        except (TimeoutException, NoSuchElementException, ElementClickInterceptedException) as e:
            if attempt < max_attempts:
                logger.warning(f"[Click] Erro na tentativa {attempt}/{max_attempts}. Retentando em {retry_delay}s...")
                time.sleep(retry_delay)
                continue
            
            logger.error(f"[Click] Erro após {max_attempts} tentativas: {e}")
            if continue_on_error:
                return False
            raise
        
        except Exception as e:
            logger.error(f"[Click] Erro inesperado: {e}")
            if continue_on_error:
                return False
            raise
    
    return False


# ==============================================================================
# FUNÇÃO: type_into()
# ==============================================================================

def type_into(
    driver,
    selector: str,
    text: str,
    selector_type=By.XPATH,
    clear_before: bool = True,
    click_before: bool = True,
    delay_before: float = 0.2,
    delay_after: float = 0.3,
    delay_between_keys: float = 0,
    timeout: int = 10,
    continue_on_error: bool = False,
    verify_text: bool = False,
    retry_count: int = 0
) -> bool:
    """
    Digita texto em um campo com opções avançadas estilo UiPath.
    
    Args:
        driver: Instância do WebDriver
        selector: Seletor do campo
        selector_type: Tipo do seletor
        text: Texto a ser digitado
        clear_before: Limpa campo antes de digitar
        click_before: Clica no campo antes de digitar
        delay_before: Delay antes da ação
        delay_after: Delay após a ação
        delay_between_keys: Delay entre cada tecla (0 = instantâneo)
        timeout: Tempo máximo para encontrar elemento
        continue_on_error: Se True, não lança exceção
        verify_text: Se True, verifica se texto foi digitado corretamente
        retry_count: Tentativas se verify falhar
        
    Returns:
        bool: True se sucesso, False se falha
    """
    attempt = 0
    max_attempts = retry_count + 1
    
    while attempt < max_attempts:
        try:
            attempt += 1
            
            # Delay antes
            if delay_before > 0:
                time.sleep(delay_before)
            
            # Encontra elemento
            logger.trace(f"[TypeInto] Procurando campo: {selector[:60]}...")
            wait = WebDriverWait(driver, timeout)
            elemento = wait.until(EC.visibility_of_element_located((selector_type, selector)))
            
            # Clica antes (se configurado)
            if click_before:
                elemento.click()
            
            # Limpa campo (se configurado)
            if clear_before:
                elemento.clear()
            
            # Digita texto
            if delay_between_keys > 0:
                for char in text:
                    elemento.send_keys(char)
                    time.sleep(delay_between_keys)
            else:
                elemento.send_keys(text)
            
            logger.trace("[TypeInto] Texto digitado.")
            # Delay após
            if delay_after > 0:
                time.sleep(delay_after)
            
            # Verificação de texto
            if verify_text:
                valor_atual = elemento.get_attribute("value") or ""
                if valor_atual == text:
                    logger.success("[TypeInto] Validação concluída com sucesso.")
                    return True
                else:
                    if attempt < max_attempts:
                        logger.warning(f"[TypeInto] Validação falhou. Esperado: {text}. Obtido: {valor_atual}. Tentativa {attempt}/{max_attempts}")
                        time.sleep(0.5)
                        continue
                    else:
                        logger.error(f"[TypeInto] Validação falhou após {max_attempts} tentativas")
                        if continue_on_error:
                            return False
                        raise ValueError(f"Texto não corresponde. Esperado: '{text}', Obtido: '{valor_atual}'")
            
            logger.success(f"[TypeInto] Sucesso.")
            return True
            
        except Exception as e:
            logger.error(f"[TypeInto] Erro: {e}")
            if continue_on_error:
                return False
            raise
    
    return False


# ==============================================================================
# FUNÇÃO: select_item()
# ==============================================================================

def select_item(
    driver,
    selector: str,
    item: str,
    selector_type=By.XPATH,
    select_by: str = "text",
    delay_before: float = 0,
    delay_after: float = 0.3,
    timeout: int = 10,
    continue_on_error: bool = False
) -> bool:
    """
    Seleciona um item em um dropdown/select estilo UiPath.
    
    Args:
        driver: Instância do WebDriver
        selector: Seletor do elemento select
        selector_type: Tipo do seletor
        item: Texto, value ou índice do item
        select_by: "text", "value" ou "index"
        delay_before: Delay antes da ação
        delay_after: Delay após a ação
        timeout: Tempo máximo para encontrar elemento
        continue_on_error: Se True, não lança exceção
        
    Returns:
        bool: True se sucesso, False se falha
    """
    try:
        # Delay antes
        if delay_before > 0:
            time.sleep(delay_before)
        
        # Encontra elemento
        logger.trace(f"[SelectItem] Procurando select: {selector[:60]}...")
        wait = WebDriverWait(driver, timeout)
        elemento = wait.until(EC.presence_of_element_located((selector_type, selector)))
        
        # Cria objeto Select
        select = Select(elemento)
        
        # Seleciona item baseado no tipo
        if select_by == "text":
            select.select_by_visible_text(item)
            logger.trace(f"[SelectItem] Selecionado por texto: '{item}'")
        elif select_by == "value":
            select.select_by_value(item)
            logger.trace(f"[SelectItem] Selecionado por value: '{item}'")
        elif select_by == "index":
            select.select_by_index(int(item))
            logger.trace(f"[SelectItem] Selecionado por índice: {item}")
        
        # Delay após
        if delay_after > 0:
            time.sleep(delay_after)
        
        logger.success(f"[SelectItem] Sucesso.")
        return True
        
    except Exception as e:
        logger.error(f"[SelectItem] Erro: {e}")
        if continue_on_error:
            return False
        raise


# ==============================================================================
# FUNÇÃO: wait_element()
# ==============================================================================

def wait_element(
    driver,
    selector: str,
    selector_type=By.XPATH,
    condition: str = "visible",
    timeout: int = 10,
    continue_on_error: bool = False
):
    """
    Aguarda um elemento com condição específica.
    
    Args:
        driver: Instância do WebDriver
        selector: Seletor do elemento
        selector_type: Tipo do seletor
        condition: "visible", "clickable", "present", "invisible"
        timeout: Tempo máximo de espera
        continue_on_error: Se True, não lança exceção
        
    Returns:
        WebElement ou None: Elemento encontrado ou None se falha
    """
    try:
        logger.trace(f"[WaitElement] Aguardando ({condition}): {selector[:60]}...")
        wait = WebDriverWait(driver, timeout)
        
        if condition == "visible":
            elemento = wait.until(EC.visibility_of_element_located((selector_type, selector)))
        elif condition == "clickable":
            elemento = wait.until(EC.element_to_be_clickable((selector_type, selector)))
        elif condition == "present":
            elemento = wait.until(EC.presence_of_element_located((selector_type, selector)))
        elif condition == "invisible":
            wait.until(EC.invisibility_of_element_located((selector_type, selector)))
            logger.success(f"[WaitElement] Elemento ficou invisível.")
            return True
        else:
            raise ValueError(f"Condição inválida: {condition}")
        
        logger.success(f"[WaitElement] Elemento encontrado.")
        return elemento
        
    except TimeoutException:
        logger.error(f"[WaitElement] Timeout após {timeout}s")
        if continue_on_error:
            return None
        raise
    except Exception as e:
        logger.error(f"[WaitElement] Erro: {e}")
        if continue_on_error:
            return None
        raise


# ==============================================================================
# FUNÇÃO: kill_process()
# ==============================================================================

def kill_process(
    process_name: str,
    friendly_name: Optional[str] = None,
    continue_on_error: bool = True
) -> bool:
    """
    Encerra um processo pelo nome, estilo UiPath Kill Process.
    
    Args:
        process_name: Nome do executável (ex: chrome.exe)
        friendly_name: Nome amigável para logs (ex: Google Chrome)
        continue_on_error: Se True, não lança exceção em caso de erro
        
    Returns:
        bool: True se o processo foi encerrado ou não estava rodando, False se erro
        
    Exemplo:
        kill_process("chrome.exe", "Google Chrome")
        kill_process("EXCEL.EXE")
    """
    display_name = friendly_name or process_name
    
    try:
        # Verificar se o processo está rodando
        check_cmd = f'tasklist /FI "IMAGENAME eq {process_name}" /NH'
        result = subprocess.run(
            check_cmd,
            shell=True,
            capture_output=True,
            text=True,
            encoding='cp850',  # Encoding padrão do Windows BR
            errors='ignore'
        )
        
        # Se o processo não está na lista, não há nada a fazer
        if process_name.lower() not in result.stdout.lower():
            logger.debug(f"[KillProcess] {display_name} não está em execução.")
            return True
        
        # Encerrar o processo forçadamente
        kill_cmd = f'taskkill /F /IM {process_name}'
        result = subprocess.run(
            kill_cmd,
            shell=True,
            capture_output=True,
            text=True,
            encoding='cp850',
            errors='ignore'
        )
        
        if result.returncode == 0:
            logger.success(f"[KillProcess] {display_name} encerrado com sucesso.")
            return True
        else:
            logger.warning(f"[KillProcess] Erro ao encerrar {display_name}: {result.stderr}")
            if continue_on_error:
                return False
            raise RuntimeError(f"Falha ao encerrar {display_name}: {result.stderr}")
            
    except Exception as e:
        logger.error(f"[KillProcess] Exceção ao tentar encerrar {display_name}: {e}")
        if continue_on_error:
            return False
        raise


# ==============================================================================
# FUNÇÃO: kill_all_processes()
# ==============================================================================

def kill_all_processes(
    config_file: Optional[str] = None,
    continue_on_error: bool = True
) -> Dict[str, bool]:
    """
    Encerra todos os processos configurados no arquivo JSON.
    
    Args:
        config_file: Caminho para arquivo JSON de configuração.
                     Se não fornecido, usa config/processes_to_kill.json
        continue_on_error: Se True, continua mesmo se algum processo falhar
        
    Returns:
        Dict[str, bool]: Dicionário com {nome_processo: sucesso}
        
    Exemplo:
        # Usando configuração padrão
        kill_all_processes()
        
        # Usando arquivo customizado
        kill_all_processes("meu_config.json")
        
    Formato do arquivo JSON:
        {
            "processes": [
                {"name": "chrome.exe", "friendly_name": "Google Chrome"},
                {"name": "msedge.exe", "friendly_name": "Microsoft Edge"}
            ]
        }
    """
    # Determinar caminho do arquivo de configuração
    if config_file:
        config_path = Path(config_file)
    else:
        # Caminho padrão: config/processes_to_kill.json
        config_path = Path(__file__).parent.parent / "config" / "processes_to_kill.json"
    
    results = {}
    
    # Verificar se arquivo existe
    if not config_path.exists():
        logger.warning(f"[KillAllProcesses] Arquivo de configuração não encontrado: {config_path}")
        return results
    
    try:
        # Ler configuração
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        processes = config.get("processes", [])
        
        if not processes:
            logger.info("[KillAllProcesses] Nenhum processo configurado para encerrar.")
            return results
        
        logger.info(f"[KillAllProcesses] Encerrando {len(processes)} processo(s) configurado(s)...")
        
        for proc in processes:
            name = proc.get("name")
            friendly_name = proc.get("friendly_name", name)
            
            if name:
                success = kill_process(name, friendly_name, continue_on_error)
                results[friendly_name] = success
        
        # Log resumo
        closed = sum(1 for v in results.values() if v)
        failed = len(results) - closed
        logger.info(f"[KillAllProcesses] Concluído: {closed} encerrado(s), {failed} com falha.")
        
        return results
        
    except json.JSONDecodeError as e:
        logger.error(f"[KillAllProcesses] Erro ao ler JSON: {e}")
        if continue_on_error:
            return results
        raise
    except Exception as e:
        logger.error(f"[KillAllProcesses] Erro inesperado: {e}")
        if continue_on_error:
            return results
        raise

