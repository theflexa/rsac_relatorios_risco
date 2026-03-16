from rsac_relatorios_risco.web.selectors_config import (
    Screen_RsaExportacao,
    Screen_RsaFiltros,
    is_pending_selector,
)


def test_pending_selectors_are_explicitly_marked_for_later_fill():
    assert is_pending_selector(Screen_RsaFiltros.INPUT_COMPETENCIA)
    assert is_pending_selector(Screen_RsaExportacao.BTN_EXPORTAR)
