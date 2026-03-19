import numpy as np
import time
import pyautogui
import cv2

from pywinauto import Application
from pathlib import Path
from loguru import logger

import pyautogui
import time
from PIL import ImageChops, ImageStat

def verificar_campo_muda_de_cor(coord, delay_clique=0.7, threshold=30):
    """
    Recebe um dicionário com l, t, r, b. Clica no centro do retângulo e verifica se mudou de cor.
    Retorna True se mudou de cor, False caso contrário.
    """
    x = (coord['l'] + coord['r']) // 2
    y = (coord['t'] + coord['b']) // 2
    left = coord['l']
    top = coord['t']
    largura = coord['r'] - coord['l']
    altura = coord['b'] - coord['t']
    img_antes = pyautogui.screenshot(region=(left, top, largura, altura))
    pyautogui.moveTo(x, y)
    pyautogui.click(x, y)
    time.sleep(delay_clique)
    img_depois = pyautogui.screenshot(region=(left, top, largura, altura))
    diff = ImageChops.difference(img_antes, img_depois)
    stat = ImageStat.Stat(diff)
    return sum(stat.mean) > threshold

def find_edit_by_rect(win, target_bounds, tolerance=2, timeout=30.0, retry_delay=0.5):
    """
    Tenta localizar um campo Edit próximo aos bounds desejados, com tolerância e timeout.
    Retorna o edit encontrado ou lança RuntimeError após o timeout.
    """
    logger.info(f"[TRACE] Buscando por campo em {target_bounds} com tolerância ±{tolerance} (timeout={timeout}s)")
    start_time = time.time()
    last_exception = None

    while True:
        edits = win.descendants(control_type="Edit")
        for edit in edits:
            try:
                r = edit.rectangle()
                #print(f"→ Encontrado: {r.left}, {r.top}, {r.right}, {r.bottom} — texto: '{edit.window_text()}'")
                if (
                    abs(r.left - target_bounds[0]) <= tolerance and
                    abs(r.top - target_bounds[1]) <= tolerance and
                    abs(r.right - target_bounds[2]) <= tolerance and
                    abs(r.bottom - target_bounds[3]) <= tolerance
                ):
                    print("[TRACE] Match encontrado.")
                    return edit
            except Exception as e:
                logger.error(f"[ERROR] Erro ao acessar .rectangle(): {e}")
                last_exception = e
        if time.time() - start_time > timeout:
            msg = f"Nenhum Edit encontrado próximo a {target_bounds} após {timeout}s"
            if last_exception:
                msg += f" | Último erro: {last_exception}"
            raise RuntimeError(msg)
        time.sleep(retry_delay)

def find_and_click_by_rect(win, target_bounds, tolerance=2):
    """
    Encontra um elemento (botão, imagem, etc.) por suas coordenadas e clica nele.
    """
    logger.debug(f"Tentando encontrar e clicar em um elemento nas coordenadas: {target_bounds}")
    
    # Busca por qualquer descendente que tenha um retângulo correspondente
    for elem in win.descendants():
        try:
            r = elem.rectangle()
            if (
                abs(r.left - target_bounds[0]) <= tolerance and
                abs(r.top - target_bounds[1]) <= tolerance and
                abs(r.right - target_bounds[2]) <= tolerance and
                abs(r.bottom - target_bounds[3]) <= tolerance
            ):
                logger.success(f"Elemento '{elem.element_info.name}' encontrado em {r}. Clicando...")
                elem.click_input()
                return # Sai da função após clicar
        except Exception:
            continue

    raise RuntimeError(f"Nenhum elemento clicável encontrado próximo a {target_bounds}")

def get_position_img(
    template_path: str | Path,
    offset_x: int = None,
    offset_y: int = None,
    threshold: float = 0.85,
    screenshot_region: tuple | None = None,
    timeout: float = 30.0,
    retry_delay: float = 0.8
) -> tuple[str, tuple[int, int]] | None:
    """
    Retorna (template_path, (x, y)) se encontrar; lança RuntimeError no timeout.
    """
    template = cv2.imread(str(template_path), cv2.IMREAD_COLOR)
    if template is None:
        print(f"[ERRO][get_position_img] Template não encontrado ou inválido: {template_path}")
        return None
    h, w, _ = template.shape

    start_time = time.time()
    while True:
        if screenshot_region:
            screenshot = pyautogui.screenshot(region=screenshot_region)
        else:
            screenshot = pyautogui.screenshot()
        screenshot_np = np.array(screenshot)
        screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)

        result = cv2.matchTemplate(screenshot_bgr, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        if max_val >= threshold:
                x, y = max_loc
                if offset_x is None:
                    offset_x = w // 2
                if offset_y is None:
                    offset_y = h // 2
                click_x = x + offset_x
                click_y = y + offset_y
                if screenshot_region:
                    left, top, _, _ = screenshot_region
                    click_x += left
                    click_y += top
                screen_width, screen_height = pyautogui.size()
                click_x = min(max(click_x, 0), screen_width-1)
                click_y = min(max(click_y, 0), screen_height-1)
                print(f"[MATCH][get_position_img] {template_path} -> ({click_x}, {click_y}) Confiança: {max_val:.3f}")
                return str(template_path), (click_x, click_y)

        if time.time() - start_time > timeout:
            msg = f"[TIMEOUT][get_position_img] {template_path} Não encontrado após {timeout}s. Max confiança: {max_val:.3f}"
            logger.error(msg)
            raise RuntimeError(msg)
        time.sleep(retry_delay)

def get_position_img_ordered(
    template_path: str | Path,
    offset_x: int = None,
    offset_y: int = None,
    threshold: float = 0.85,
    screenshot_region: tuple | None = None,
    timeout: float = 30.0,
    retry_delay: float = 0.8
) -> tuple[str, tuple[int, int]] | None:
    """
    Retorna (template_path, (x, y)) se encontrar; lança RuntimeError no timeout.
    Busca a primeira ocorrência de cima para baixo quando há múltiplas correspondências.
    """
    template = cv2.imread(str(template_path), cv2.IMREAD_COLOR)
    if template is None:
        print(f"[ERRO][get_position_img_ordered] Template não encontrado ou inválido: {template_path}")
        return None
    h, w, _ = template.shape

    start_time = time.time()
    while True:
        if screenshot_region:
            screenshot = pyautogui.screenshot(region=screenshot_region)
        else:
            screenshot = pyautogui.screenshot()
        screenshot_np = np.array(screenshot)
        screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)

        result = cv2.matchTemplate(screenshot_bgr, template, cv2.TM_CCOEFF_NORMED)
        
        # Encontrar todas as posições que atendem ao threshold
        locations = np.where(result >= threshold)
        if len(locations[0]) > 0:
            # Ordenar por coordenada Y (de cima para baixo)
            matches = list(zip(locations[1], locations[0]))  # (x, y)
            matches.sort(key=lambda match: match[1])  # Ordenar por Y
            
            # Pegar a primeira posição (mais acima)
            x, y = matches[0]
            
            # Calcular o centro exato da imagem encontrada
            if offset_x is None:
                offset_x = w // 2
            if offset_y is None:
                offset_y = h // 2
            
            # Coordenadas do centro da imagem
            click_x = x + offset_x
            click_y = y + offset_y
            
            # Ajustar para screenshot_region se necessário
            if screenshot_region:
                left, top, _, _ = screenshot_region
                click_x += left
                click_y += top
            screen_width, screen_height = pyautogui.size()
            click_x = min(max(click_x, 0), screen_width-1)
            click_y = min(max(click_y, 0), screen_height-1)
            
            confidence = result[y, x]
            print(f"[MATCH][get_position_img_ordered] {template_path} -> ({click_x}, {click_y}) Confiança: {confidence:.3f} (primeira de {len(matches)} encontradas)")
            return str(template_path), (click_x, click_y)

        if time.time() - start_time > timeout:
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            msg = f"[TIMEOUT][get_position_img_ordered] {template_path} Não encontrado após {timeout}s. Max confiança: {max_val:.3f}"
            logger.error(msg)
            raise RuntimeError(msg)
        time.sleep(retry_delay)

def find_first_template_match(templates, threshold=0.85, timeout=30.0, retry_delay=0.8, screenshot_region=None, offset_x=None, offset_y=None):
    """
    Loop único: tira screenshot, testa todos os templates no mesmo frame, retorna o primeiro match.
    Não trava, não espera timeout de outros.
    """
    # Carrega todos os templates antes do loop
    loaded_templates = []
    for template_path in templates:
        template = cv2.imread(str(template_path), cv2.IMREAD_COLOR)
        if template is None:
            print(f"[ERRO] Template não encontrado: {template_path}")
            continue
        h, w, _ = template.shape
        loaded_templates.append((str(template_path), template, w, h))
    if not loaded_templates:
        msg = "[ERRO] Nenhum template carregado."
        logger.error(msg)
        raise RuntimeError(msg)

    start_time = time.time()
    while True:
        # Screenshot de toda a tela ou da região especificada
        if screenshot_region:
            screenshot = pyautogui.screenshot(region=screenshot_region)
        else:
            screenshot = pyautogui.screenshot()
        screenshot_np = np.array(screenshot)
        screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)

        # Testa todos os templates no mesmo frame
        for template_path, template, w, h in loaded_templates:
            result = cv2.matchTemplate(screenshot_bgr, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            if max_val >= threshold:
                x, y = max_loc
                ox = w // 2 if offset_x is None else offset_x
                oy = h // 2 if offset_y is None else offset_y
                click_x = x + ox
                click_y = y + oy
                screen_width, screen_height = pyautogui.size()
                click_x = min(max(click_x, 0), screen_width-1)
                click_y = min(max(click_y, 0), screen_height-1)
                print(f"[MATCH] {template_path} -> ({click_x}, {click_y}) Confiança: {max_val:.3f}")
                return template_path, (click_x, click_y)
        if time.time() - start_time > timeout:
            msg = f"[TIMEOUT] Nenhum template deu match após {timeout}s."
            logger.error(msg)
            raise RuntimeError(msg)
        time.sleep(retry_delay)

def click_and_verify(
    img_click,
    img_verify,
    *,
    offset_x=None,
    offset_y=None,
    click_threshold=0.77,
    verify_threshold=0.77,
    click_timeout=5,
    verify_timeout=10,
    total_timeout=30,
    delay_after_click=0.3
):
    """
    Tenta clicar e verificar múltiplas vezes, até confirmar (ou estourar o timeout total).
    """
    import time
    import pyautogui

    start_time = time.time()
    attempt = 1

    while time.time() - start_time < total_timeout:
        print(f"[INFO] Tentativa {attempt} de clique em {img_click}")
        try:
            result = get_position_img(
                img_click,
                offset_x=offset_x,
                offset_y=offset_y,
                threshold=click_threshold,
                timeout=click_timeout,
            )
        except RuntimeError as e:
            print(f"[ERROR] Falha ao localizar imagem para clique (tentativa {attempt}): {e}")
            attempt += 1
            continue
        if not result:
            print(f"[WARN] Não encontrou imagem para clicar: {img_click}")
            # Decide se sai ou tenta de novo; aqui apenas segue tentando
            attempt += 1
            continue

        _, (x, y) = result
        try:
            pyautogui.click(x, y)
        except Exception as e:
            print(f"[ERROR] Erro ao clicar em ({x}, {y}) na tentativa {attempt}: {e}")
            attempt += 1
            continue
        time.sleep(delay_after_click)

        # Verifica se o alvo apareceu dentro de verify_timeout
        t0 = time.time()
        while time.time() - t0 < verify_timeout:
            try:
                verify_result = get_position_img(
                    img_verify,
                    threshold=verify_threshold,
                    timeout=1,
                )
            except RuntimeError as e:
                print(f"[WARN] Erro durante verificação da imagem alvo: {e}")
                verify_result = None
            if verify_result:
                print(f"[SUCESSO] Verificação positiva após clique em {img_click}")
                return True
            time.sleep(0.3)
        
        print(f"[WARN] Não confirmou ação após clique em {img_click}, tentando novamente...")
        attempt += 1

    msg = f"Timeout total ({total_timeout}s) ao tentar clicar/verificar {img_click}"
    logger.error(f"{msg}")
    raise RuntimeError(msg)

def click_coords_and_verify(
    coords,
    img_verify,
    *,
    verify_threshold=0.87,
    verify_timeout=10,
    delay_after_click=0.3
):
    """
    Clica nas coordenadas fornecidas e espera o template de verificação aparecer.
    """
    import time
    import pyautogui
    from .helpers import get_position_img

    pyautogui.click(coords[0], coords[1])
    time.sleep(delay_after_click)
    t0 = time.time()
    while time.time() - t0 < verify_timeout:
        try:
            verify_result = get_position_img(img_verify, threshold=verify_threshold, timeout=1)
        except RuntimeError as e:
            print(f"[WARN] Erro durante verificação da imagem alvo: {e}")
            verify_result = None
        if verify_result:
            return True
        time.sleep(0.3)
    msg = f"Timeout ({verify_timeout}s) ao verificar imagem {img_verify} após clique em coords {coords}"
    logger.error(msg)
    raise RuntimeError(msg)

def click_and_verify_with_bounds(
    img_click,
    img_verify,
    *,
    offset_x=None,
    offset_y=None,
    click_threshold=0.87,
    verify_threshold=0.87,
    click_timeout=5,
    verify_timeout=10,
    total_timeout=30,
    delay_after_click=0.3
):
    """
    Igual ao click_and_verify, mas retorna também as coordenadas do clique e os bounds
    estimados do template clicado no momento do sucesso.

    Returns:
        (success: bool, click_xy: tuple|None, bounds: tuple|None)
        bounds no formato (left, top, right, bottom)
    """
    import time
    import pyautogui
    import cv2

    start_time = time.time()
    attempt = 1

    while time.time() - start_time < total_timeout:
        print(f"[INFO] Tentativa {attempt} de clique em {img_click}")
        try:
            result = get_position_img(
                img_click,
                offset_x=offset_x,
                offset_y=offset_y,
                threshold=click_threshold,
                timeout=click_timeout,
            )
        except RuntimeError as e:
            print(f"[ERROR] Falha ao localizar imagem para clique (tentativa {attempt}): {e}")
            attempt += 1
            continue
        if not result:
            print(f"[WARN] Não encontrou imagem para clicar: {img_click}")
            attempt += 1
            continue

        template_path, (x, y) = result
        try:
            pyautogui.click(x, y)
        except Exception as e:
            print(f"[ERROR] Erro ao clicar em ({x}, {y}) na tentativa {attempt}: {e}")
            attempt += 1
            continue
        time.sleep(delay_after_click)

        # Verifica se o alvo apareceu dentro de verify_timeout
        t0 = time.time()
        while time.time() - t0 < verify_timeout:
            try:
                verify_result = get_position_img(
                    img_verify,
                    threshold=verify_threshold,
                    timeout=1,
                )
            except RuntimeError as e:
                print(f"[WARN] Erro durante verificação da imagem alvo: {e}")
                verify_result = None
            if verify_result:
                # Estima bounds a partir do tamanho do template clicado
                tpl = cv2.imread(str(template_path), cv2.IMREAD_COLOR)
                h, w = (tpl.shape[0], tpl.shape[1]) if tpl is not None else (0, 0)
                ox = (w // 2) if offset_x is None else offset_x
                oy = (h // 2) if offset_y is None else offset_y
                left = x - ox
                top = y - oy
                right = x + (w - ox)
                bottom = y + (h - oy)
                print(f"[SUCESSO] Verificação positiva. Clique em ({x}, {y}) bounds=({left},{top},{right},{bottom})")
                return True, (x, y), (left, top, right, bottom)
            time.sleep(0.3)

        print(f"[WARN] Não confirmou ação após clique em {img_click}, tentando novamente...")
        attempt += 1

    msg = f"Timeout total ({total_timeout}s) ao tentar clicar/verificar {img_click}"
    logger.error(f"{msg}")
    raise RuntimeError(msg)


def click_coords_and_verify_double(
    coords,
    img_verify,
    *,
    verify_threshold=0.87,
    verify_timeout=10,
    delay_after_click=0.3
):
    """
    Executa clique duplo nas coordenadas fornecidas e espera o template de verificação aparecer.
    """
    import time
    import pyautogui
    from .helpers import get_position_img

    pyautogui.doubleClick(coords[0], coords[1])
    time.sleep(delay_after_click)
    t0 = time.time()
    while time.time() - t0 < verify_timeout:
        try:
            verify_result = get_position_img(img_verify, threshold=verify_threshold, timeout=1)
        except RuntimeError as e:
            print(f"[WARN] Erro durante verificação da imagem alvo: {e}")
            verify_result = None
        if verify_result:
            return True
        time.sleep(0.3)
    msg = f"Timeout ({verify_timeout}s) ao verificar imagem {img_verify} após duplo clique em coords {coords}"
    logger.error(msg)
    raise RuntimeError(msg)


def scroll_until_find_image(
    target_image,
    *,
    max_attempts=20,
    scroll_amount=-500,
    scroll_delay=1.0,
    search_timeout=2.0,
    threshold=0.85
):
    """
    Faz scroll na página até encontrar uma imagem específica.
    
    Args:
        target_image: Caminho para a imagem a ser encontrada
        max_attempts: Número máximo de tentativas de scroll
        scroll_amount: Quantidade de scroll (negativo para baixo, positivo para cima)
        scroll_delay: Delay entre scrolls para carregar a página
        search_timeout: Timeout para verificar se a imagem aparece
        threshold: Threshold para reconhecimento da imagem
    
    Returns:
        tuple: (sucesso, tentativas_usadas) onde sucesso é bool
    """
    import time
    import pyautogui
    
    print(f"[INFO] Iniciando scroll até encontrar: {target_image}")
    
    def tentar_encontrar_no_frame(timeout_seg: float):
        inicio = time.time()
        template = cv2.imread(str(target_image), cv2.IMREAD_COLOR)
        if template is None:
            print(f"[ERRO][scroll_until_find_image] Template inválido: {target_image}")
            return None
        h, w, _ = template.shape
        while time.time() - inicio < timeout_seg:
            screenshot = pyautogui.screenshot()
            frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            result = cv2.matchTemplate(frame, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)
            if max_val >= threshold:
                x, y = max_loc
                cx = x + (w // 2)
                cy = y + (h // 2)
                sw, sh = pyautogui.size()
                cx = min(max(cx, 0), sw - 1)
                cy = min(max(cy, 0), sh - 1)
                print(f"[MATCH][scroll_until_find_image] {target_image} -> ({cx}, {cy}) Confiança: {max_val:.3f}")
                return (cx, cy)
            time.sleep(0.2)
        return None

    for attempt in range(max_attempts):
        pos = tentar_encontrar_no_frame(search_timeout)
        if pos:
            print(f"[SUCESSO] Imagem '{target_image}' encontrada após {attempt + 1} tentativas de scroll")
            return True, attempt + 1
        
        print(f"[INFO] Tentativa {attempt + 1}/{max_attempts}: Fazendo scroll...")
        pyautogui.scroll(scroll_amount)
        time.sleep(scroll_delay)
    
    msg = f"Imagem '{target_image}' não encontrada após {max_attempts} tentativas de scroll"
    logger.error(msg)
    return False, max_attempts

def get_element_name_by_point(app_title: str, x: int, y: int) -> str:
    # Conecta ao aplicativo pelo título
    app = Application(backend="uia").connect(title_re=app_title)
    win = app.window(title_re=app_title)

    # Localiza o elemento na coordenada
    elem = win.from_point(x, y)

    # Retorna a propriedade 'name'
    return elem.element_info.name
    
def get_element_name_by_rect(app_title: str, left: int, top: int, right: int, bottom: int, tolerance: int = 2) -> str:
    """
    Retorna o 'name' do primeiro elemento cujo BoundingRectangle corresponde aos limites fornecidos
    dentro de uma tolerância em pixels.
    """
    app = Application(backend="uia").connect(title_re=app_title)
    win = app.window(title_re=app_title)

    for elem in win.descendants():
        
        r = elem.rectangle()
        if (
            abs(r.left - left) <= tolerance and
            abs(r.top - top) <= tolerance and
            abs(r.right - right) <= tolerance and
            abs(r.bottom - bottom) <= tolerance
        ):
            return elem.element_info.name

def double_click_coords(x, y, delay=0.05):
    """
    Executa um duplo clique nas coordenadas (x, y).
    """
    pyautogui.moveTo(x, y)
    pyautogui.doubleClick(x, y)
    time.sleep(delay)

def verificar_mudanca_cor_dinamica(region, delay_clique=0.7, threshold=0.85):
    """
    Verifica se houve mudança de cor na tela após pressionar uma tecla.
    Captura screenshot antes e depois da ação e compara as diferenças.
    
    Args:
        region (tuple, optional): Região para verificação no formato (left, top, right, bottom).
                                 Se None, usa a região padrão {l:816, t:416, r:1291, b:799}.
        delay_clique (float): Tempo de espera após pressionar a tecla.
        threshold (int): Limite para considerar que houve mudança.
    
    Returns:
        bool: True se mudou de cor, False caso contrário.
    """
    
    # Converte para formato pyautogui (left, top, width, height)
    left, top, right, bottom = region
    pyautogui_region = (left, top, right - left, bottom - top)
    
    # Captura screenshot antes da ação (apenas da região específica)
    img_antes = pyautogui.screenshot(region=pyautogui_region)
    
    # Pressiona a tecla down
    pyautogui.press('down')
    time.sleep(delay_clique)
    
    # Captura screenshot depois da ação (apenas da região específica)
    img_depois = pyautogui.screenshot(region=pyautogui_region)
    
    # Calcula a diferença entre as imagens
    diff = ImageChops.difference(img_antes, img_depois)
    stat = ImageStat.Stat(diff)
    
    # Retorna True se a diferença for maior que o threshold
    return sum(stat.mean) > threshold

def buscar_com_scroll(img_cinza, img_claro, screenshot_region=None):
    """
    Função auxiliar para buscar imagem com scroll dinâmico.
    
    Args:
        img_cinza: Caminho para a imagem cinza a ser procurada
        img_claro: Caminho para a imagem clara a ser procurada
        screenshot_region: Região da tela para captura (opcional)
    
    Returns:
        Posição da imagem encontrada ou None
    """
    from pathlib import Path
    
    # Caminho para a imagem de scroll
    current_file = Path(__file__).resolve()
    lib_project_root = current_file.parent.parent.parent.parent
    ocr_credito = (lib_project_root / "src" / "lib_sisbr_desktop" / "ocr" / "plataforma_de_credito").resolve()
    scroll_img = ocr_credito / "scroll.png"
    
    try:
        pos = get_position_img(img_cinza, timeout=6, threshold=0.85, screenshot_region=screenshot_region)
    except RuntimeError:
        pos = None
    if pos:
        return pos

    def hover_scroll():
        try:
            scroll_pos = get_position_img(scroll_img, timeout=6, threshold=0.95)
        except RuntimeError:
            scroll_pos = None
        if scroll_pos:
            pyautogui.moveTo(scroll_pos[1])

    # Hover e Scroll total para baixo
    hover_scroll()
    pyautogui.scroll(-10000)
    try:
        pos = get_position_img(img_cinza, timeout=6, threshold=0.85, screenshot_region=screenshot_region)
    except RuntimeError:
        pos = None
    if pos:
        return pos

    # Hover e Scroll menor para cima
    hover_scroll()
    pyautogui.scroll(550)
    try:
        pos = get_position_img(img_cinza, timeout=6, threshold=0.85, screenshot_region=screenshot_region)
    except RuntimeError:
        pos = None
    if pos:
        return pos

    # Hover e Reset scroll total para cima
    hover_scroll()
    pyautogui.scroll(10000)

    try:
        pos = get_position_img(img_claro, timeout=6, threshold=0.85, screenshot_region=screenshot_region)
    except RuntimeError:
        pos = None
    if pos:
        return pos
    return None