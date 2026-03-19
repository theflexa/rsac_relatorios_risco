
from ..gui.helpers import get_position_img, find_first_template_match, click_and_verify
from pathlib import Path
import pyautogui

def error_handler(win) -> bool:
    from loguru import logger
    #fecha popups, reinicializa tela, limpa buffers etc

    # Caminho dos templates
    current_file = Path(__file__).resolve()
    # parent.parent = .../lib_sisbr_desktop
    lib_project_root = current_file.parent.parent
    ocr_path = (lib_project_root / "ocr" / "handlers").resolve()

    fatal_templates = [
        ocr_path / "erro_interno_1009.png",
        ocr_path / "adobe_air.png",
        ocr_path / "JDBC.png",
        ocr_path / "erro.png",
        # Adicione outros templates fatais aqui
    ]

    popup_templates = [
        ocr_path / "fechar1.png",
        ocr_path / "fechar2.png",
        ocr_path / "fechar3.png",
        ocr_path / "fechar4.png",
        ocr_path / "fechar5.png",
        ocr_path / "informe_cooperado.png",
        ocr_path / "alert.png",
        ocr_path / "ok.png",
        ocr_path / "fechar.png",
        ocr_path / "continue.png",
        ocr_path / "dimiss_all.png",
        # Adicione outros pop-ups aqui
    ]

    # Procura por pop-ups normais primeiro
    result = find_first_template_match(popup_templates, threshold=0.90, timeout=10)
    if result:
        template_found, pos = result
        logger.info(f"Pop-up encontrado: {template_found} {pos}")
        pyautogui.click(pos)
        return True

    # Procura por templates fatais
    result = find_first_template_match(fatal_templates, threshold=0.90, timeout=10)
    if result:
        template_found, pos = result
        logger.error(f"Template FATAL encontrado: {template_found} {pos}")
        raise RuntimeError(f"Erro fatal detectado ({template_found}). É necessário reiniciar o Sisbr.")

    logger.warning("Nenhuma imagem de error_handler encontrada.")
    return False