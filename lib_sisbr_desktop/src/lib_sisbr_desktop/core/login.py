import pyautogui
from pathlib import Path

from .. import config
from lib_sisbr_desktop.src.lib_sisbr_desktop.gui.helpers import get_position_img
from lib_sisbr_desktop.src.lib_sisbr_desktop.gui.typer import write_with_retry, write_without_verify 

# Usa o mesmo .env raiz já carregado por lib_sisbr_desktop.config
repo_root = Path(config.env_path)
lib_project_root = Path(__file__).resolve().parent.parent.parent.parent
if repo_root.exists():
    print(f"[INFO][lib_sisbr_desktop.login] Usando .env raiz do projeto: {repo_root}")
else:
    print(f"[WARN][lib_sisbr_desktop.login] .env raiz do projeto não encontrado em: {repo_root}")

def _window_region(win) -> tuple[int, int, int, int] | None:
    if win is None:
        return None
    try:
        rect = win.rectangle()
        left = max(rect.left, 0)
        top = max(rect.top, 0)
        width = max(rect.right - rect.left, 1)
        height = max(rect.bottom - rect.top, 1)
        return (left, top, width, height)
    except Exception:
        return None


def login(win=None) -> bool:
    """Realiza o login no Sisbr usando credenciais do .env, template matching e offset para digitar nos campos."""

    usuario_lib = config.LOGIN_USER
    senha_lib = config.LOGIN_PASSWORD
    # Coop e npac, se for usar depois:
    # coop_lib = os.getenv("COOP")
    # npac_lib = os.getenv("NPAC")

    if not all([usuario_lib, senha_lib]):
        print(f"[ERROR][lib_sisbr_desktop.login] Credenciais (LOGIN_USER, LOGIN_PASSWORD) não configuradas no .env raiz do projeto: {repo_root}")
        return False

    print(f"[INFO][lib_sisbr_desktop.login] Tentando login com Usuário da lib: {usuario_lib}")

    # Caminho dos templates
    ocr_path = lib_project_root / "src" / "lib_sisbr_desktop" / "ocr" / "login"
    user_img = ocr_path / "user.png"
    pass_img = ocr_path / "password.png"
    screenshot_region = _window_region(win)
    # login_button_img = ocr_path / "login_button.png"  # se tiver imagem do botão

    try:
        if win is not None:
            try:
                win.set_focus()
            except Exception:
                pass

        # Ajuste os offsets conforme o centro do campo digitável em relação ao template do label
        # Exemplo: label ocupa esquerda, campo começa 120px à direita do topo do label
        _, pos = get_position_img(
            user_img,
            offset_x=120,
            offset_y=10,
            threshold=0.57,
            screenshot_region=screenshot_region,
        )
        x, y = pos
        write_with_retry(x, y, usuario_lib)

        _, pos = get_position_img(
            pass_img,
            offset_x=120,
            offset_y=10,
            threshold=0.57,
            screenshot_region=screenshot_region,
        )
        x, y = pos
        write_without_verify(x, y, senha_lib)

        # Clique no botão "LOGAR"
        pyautogui.press('tab', presses=3)  # ajusta se precisar
        pyautogui.press('enter')

        print("[INFO][lib_sisbr_desktop.login] Login: sequência executada.")
        # Não há validação visual ainda — adicione OCR ou delay se necessário
        pyautogui.sleep(2)
        return True

    except Exception as e:
        print(f"[ERROR][lib_sisbr_desktop.login] Falha no login: {e}")
        return False
