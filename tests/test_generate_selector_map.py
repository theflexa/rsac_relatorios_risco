from scripts.generate_selector_map import ROWS, build_workbook


def test_build_workbook_lists_expanded_web_selector_contract() -> None:
    workbook = build_workbook()

    instructions = workbook["Instrucoes"]
    selectors = workbook["Seletores"]

    assert instructions["A2"].value == "Preencha OuterHTML e, se souber, o seletor final."
    assert instructions["A3"].value == "O acesso ao modulo RSA vem da lib_sisbr_desktop; esta planilha lista apenas seletores web."
    assert selectors["B2"].value == "Screen_RsaHome"
    assert selectors["C2"].value == "VALIDACAO_HOME"
    assert selectors["C3"].value == "BTN_MENU_RELATORIOS"
    assert selectors["F2"].value == "https://portal.sisbr.coop.br/rsa/"
    assert selectors["F4"].value == "https://portal.sisbr.coop.br/rsa/"
    assert selectors["F5"].value == "https://portal.sisbr.coop.br/rsa/risco"
    assert selectors["F12"].value == "https://portal.sisbr.coop.br/rsa/risco - modal Opcoes de Impressao"
    assert selectors["F16"].value == "https://portal.sisbr.coop.br/rsa/risco - painel Relatorios Disponiveis"
    assert selectors["C5"].value == "VALIDACAO_TELA_FORMULARIO"
    assert selectors["C11"].value == "BTN_EXPORTAR"
    assert selectors["C15"].value == "BTN_GERAR_RELATORIO"
    assert selectors["C19"].value == "BTN_IMPRIMIR_TEMPLATE"
    assert selectors.max_row == len(ROWS) + 1
