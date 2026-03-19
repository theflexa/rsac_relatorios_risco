from pathlib import Path

from scripts.crop_selector_evidence import build_jobs


def test_build_jobs_contains_only_web_selector_crops() -> None:
    jobs = build_jobs(Path("Prints_telas/Prints_telas"), Path("temp/recortes"))
    names = [job["selector_name"] for job in jobs]

    assert "VALIDACAO_HOME" in names
    assert "BTN_MENU_RELATORIOS" in names
    assert "VALIDACAO_TELA_FORMULARIO" in names
    assert "BTN_GERAR_RELATORIO" in names
    assert "BTN_IMPRIMIR_TEMPLATE" in names
    assert "BTN_MODULO_RSA" not in names
    assert len(names) == 18
