from rsac_relatorios_risco.web.selectors_config import (
    Screen_RsaFormulario,
    Screen_RsaHome,
    Screen_RsaModalImpressao,
    Screen_RsaRelatoriosDisponiveis,
    is_pending_selector,
)


def test_core_selectors_are_resolved_from_filled_map():
    assert not is_pending_selector(Screen_RsaHome.BTN_MENU_RELATORIOS)
    assert Screen_RsaFormulario.SELECT_TIPO_RELATORIO == "tipo-relatorio"
    assert Screen_RsaFormulario.SELECT_SINGULAR == "combo-singular"
    assert Screen_RsaFormulario.INPUT_MES_ANO == "mes-ano"
    assert Screen_RsaModalImpressao.SELECT_FORMATO == "formato-impressao"
    assert Screen_RsaRelatoriosDisponiveis.TABELA_RELATORIOS == "//table[@aria-label='Tabela de Resultados']"


def test_dynamic_templates_keep_required_placeholders():
    assert "{cooperativa}" in Screen_RsaFormulario.OPCAO_SINGULAR_TEMPLATE
    assert "{relatorio}" in Screen_RsaRelatoriosDisponiveis.LINHA_RELATORIO_TEMPLATE
    assert "{situacao}" in Screen_RsaRelatoriosDisponiveis.BTN_IMPRIMIR_TEMPLATE
    assert "{tipo}" in Screen_RsaRelatoriosDisponiveis.BTN_IMPRIMIR_TEMPLATE
