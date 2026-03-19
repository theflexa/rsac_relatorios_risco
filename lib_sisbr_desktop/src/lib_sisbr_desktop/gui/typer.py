# src/lib_sisbr_desktop/gui/typer.py
from time import sleep
from pywinauto.controls.uia_controls import EditWrapper
from loguru import logger
import pyautogui
import time
import pyperclip

# Desabilita o fail-safe do PyAutoGUI para evitar interrupções quando o mouse vai para o canto
# NOTA: Isso é necessário para automação robusta, mas use com cuidado
pyautogui.FAILSAFE = False

def type_with_retry(edit_field: EditWrapper, expected_text: str, retries: int = 3, delay: float = 0.1, wait: float = 0.5):
    """
    Digita no campo editável com click + teclado + validação do valor lido.
    """
    for attempt in range(1, retries + 1):
        try:
            edit_field.set_focus()
            edit_field.click_input()
            sleep(0.2)

            edit_field.type_keys("^a{DEL}", set_foreground=True)
            sleep(0.2)

            edit_field.type_keys(expected_text, with_spaces=True, set_foreground=True, pause=0.05)
            sleep(delay)

            try:
                current = edit_field.legacy_properties().get("Value", "").strip()
            except Exception:
                current = ""

            if current == expected_text:
                logger.success(f"Texto '{expected_text}' digitado e verificado com sucesso.")
                return True
            
            logger.warning(f"[Tentativa {attempt}/{retries}] Texto incorreto: '{current}' vs esperado '{expected_text}'")
        
        except Exception as e:
            logger.error(f"Erro inesperado na tentativa {attempt}/{retries} de digitar: {e}")
        
        sleep(wait) # Espera antes de tentar novamente

    raise ValueError(f"Falha ao digitar corretamente o texto '{expected_text}' após {retries} tentativas.")

def type_simple(edit_field, text: str, delay: float = 0.1):
    """
    Digita no campo sem validação do texto digitado (usado para campos como SENHA).
    """
    edit_field.click_input()
    sleep(0.1)
    edit_field.type_keys("^a{DEL}", set_foreground=True)
    sleep(0.1)
    edit_field.type_keys(text, with_spaces=True, set_foreground=True)

def write_with_retry(
    x: int, y: int,
    expected_text: str,
    retries: int = 3,
    delay: float = 0.1,
    interval: float = 0.02
) -> bool:
    """
    Clica na coordenada, cola o texto via clipboard (preserva acentos), valida lendo do clipboard.
    Repete até sucesso ou limite de tentativas.

    x, y: coordenadas do campo
    expected_text: texto a ser digitado
    retries: tentativas
    delay: tempo entre tentativas
    interval: intervalo entre teclas
    """
    for attempt in range(1, retries + 1):
        try:
            pyautogui.click(x, y)
            time.sleep(0.2)

            # Seleciona tudo e apaga
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.05)
            pyautogui.press('backspace')
            time.sleep(0.05)

            # Cola o texto via clipboard para preservar acentos
            pyperclip.copy(expected_text)
            time.sleep(0.05)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(delay)

            # Seleciona tudo e copia para validar
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.05)
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(0.05)
            current = pyperclip.paste().strip()

            if current == expected_text:
                print(f"[SUCESSO][write_with_retry] '{expected_text}' digitado e validado.")
                return True

            print(f"[TENTATIVA {attempt}/{retries}] Texto lido: '{current}' vs esperado: '{expected_text}'")

        except Exception as e:
            print(f"[ERRO][write_with_retry][Tentativa {attempt}/{retries}] {e}")

        time.sleep(delay)
    
    raise ValueError(f"Falha ao digitar corretamente '{expected_text}' após {retries} tentativas.")

def write_without_verify(
    x: int, y: int,
    text: str,
    interval: float = 0.05
) -> None:
    """
    Clica no campo (x, y), limpa (Ctrl+A + Backspace) e digita o texto, sem verificar valor.
    Use para campos como senha, captcha, etc.
    """
    pyautogui.click(x, y)
    time.sleep(0.2)
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.05)
    pyautogui.press('backspace')
    time.sleep(0.05)
    pyautogui.write(text, interval=interval)


def write_with_retry_formatted(
    x: int, y: int,
    expected_text: str,
    retries: int = 3,
    delay: float = 0.1,
    interval: float = 0.02
) -> bool:
    """
    Clica na coordenada, digita o texto, valida lendo do clipboard.
    Aceita tanto versão formatada quanto não formatada para CPF/CNPJ.
    Repete até sucesso ou limite de tentativas.

    x, y: coordenadas do campo
    expected_text: texto a ser digitado
    retries: tentativas
    delay: tempo entre tentativas
    interval: intervalo entre teclas
    """
    import re
    
    def normalize_text(text):
        """Remove formatação de CPF/CNPJ (pontos, hífens, barras)"""
        return re.sub(r'[.\-/]', '', text)
    
    for attempt in range(1, retries + 1):
        try:
            pyautogui.click(x, y)
            time.sleep(0.2)

            # Seleciona tudo e apaga
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.05)
            pyautogui.press('backspace')
            time.sleep(0.05)

            # Digita o texto
            pyautogui.write(expected_text, interval=interval)
            time.sleep(delay)

            # Seleciona tudo e copia para validar
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.05)
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(0.05)
            current = pyperclip.paste().strip()

            # Verifica se o texto é igual (com ou sem formatação)
            if current == expected_text or normalize_text(current) == normalize_text(expected_text):
                print(f"[SUCESSO][write_with_retry_formatted] '{expected_text}' digitado e validado (atual: '{current}').")
                return True

            print(f"[TENTATIVA {attempt}/{retries}] Texto lido: '{current}' vs esperado: '{expected_text}'")

        except Exception as e:
            print(f"[ERRO][write_with_retry_formatted][Tentativa {attempt}/{retries}] {e}")

        time.sleep(delay)
    
    raise ValueError(f"Falha ao digitar corretamente '{expected_text}' após {retries} tentativas.")