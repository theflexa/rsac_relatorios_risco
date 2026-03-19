from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "Models" / "Mapa_Seletores_RSA.xlsx"

HEADERS = [
    "Ordem",
    "Tela/Classe",
    "Campo no selectors_config.py",
    "Descricao atual",
    "Acao esperada",
    "URL ou Tela onde aparece",
    "OuterHTML",
    "Tipo final",
    "Seletor final",
    "Observacoes",
]

ROWS = [
    (
        1,
        "Screen_RsaHome",
        "VALIDACAO_HOME",
        "elemento de validacao da home RSA",
        "Confirmar que a home RSA carregou",
        "https://portal.sisbr.coop.br/rsa/",
        "",
        "By.XPATH",
        "",
        "Print 3.",
    ),
    (
        2,
        "Screen_RsaHome",
        "BTN_MENU_RELATORIOS",
        "botao do menu lateral Relatorios",
        "Abrir o menu lateral de Relatorios",
        "https://portal.sisbr.coop.br/rsa/",
        "",
        "By.XPATH",
        "",
        "Print 3.",
    ),
    (
        3,
        "Screen_RsaMenuRelatorios",
        "ITEM_RELATORIOS_RSAC",
        "opcao Relatorios de Riscos Social Ambiental e Climatico",
        "Entrar na tela do formulario RSAC",
        "https://portal.sisbr.coop.br/rsa/",
        "",
        "By.XPATH",
        "",
        "Print 4.",
    ),
    (
        4,
        "Screen_RsaFormulario",
        "VALIDACAO_TELA_FORMULARIO",
        "elemento que valida a tela do formulario RSAC",
        "Confirmar que o painel do formulario foi aberto",
        "https://portal.sisbr.coop.br/rsa/risco",
        "",
        "By.XPATH",
        "",
        "Print 5.",
    ),
    (
        5,
        "Screen_RsaFormulario",
        "SELECT_TIPO_RELATORIO",
        "select do tipo de relatorio",
        "Abrir o select do tipo de relatorio",
        "https://portal.sisbr.coop.br/rsa/risco",
        "",
        "By.XPATH",
        "",
        "Print 5.",
    ),
    (
        6,
        "Screen_RsaFormulario",
        "OPCAO_TIPO_RELATORIO_RELATORIO_POR_COOPERATIVA",
        "opcao Relatorio por Cooperativa no select de tipo",
        "Selecionar o tipo Relatorio por Cooperativa",
        "https://portal.sisbr.coop.br/rsa/risco",
        "",
        "By.XPATH",
        "",
        "Print 5 preenchido.",
    ),
    (
        7,
        "Screen_RsaFormulario",
        "SELECT_SINGULAR",
        "select da singular",
        "Abrir o select da singular",
        "https://portal.sisbr.coop.br/rsa/risco",
        "",
        "By.XPATH",
        "",
        "Print 5.",
    ),
    (
        8,
        "Screen_RsaFormulario",
        "OPCAO_SINGULAR_TEMPLATE",
        "opcao da singular com {cooperativa}",
        "Selecionar a cooperativa correspondente ao item",
        "https://portal.sisbr.coop.br/rsa/risco",
        "",
        "By.XPATH",
        "",
        "Print 5 combobox. Mantenha {cooperativa} no template se o seletor for dinamico.",
    ),
    (
        9,
        "Screen_RsaFormulario",
        "INPUT_MES_ANO",
        "campo Mes/Ano",
        "Preencher o Mes/Ano da competencia",
        "https://portal.sisbr.coop.br/rsa/risco",
        "",
        "By.XPATH",
        "",
        "Print 5.",
    ),
    (
        10,
        "Screen_RsaFormulario",
        "BTN_EXPORTAR",
        "botao Exportar do formulario",
        "Abrir o modal de opcoes de impressao",
        "https://portal.sisbr.coop.br/rsa/risco",
        "",
        "By.XPATH",
        "",
        "Print 5.",
    ),
    (
        11,
        "Screen_RsaModalImpressao",
        "MODAL_OPCOES_IMPRESSAO",
        "container/modal Opcoes de Impressao",
        "Validar que o modal de impressao abriu",
        "https://portal.sisbr.coop.br/rsa/risco - modal Opcoes de Impressao",
        "",
        "By.XPATH",
        "",
        "Print 6.",
    ),
    (
        12,
        "Screen_RsaModalImpressao",
        "SELECT_FORMATO",
        "select Formato no modal de impressao",
        "Abrir o select de formato",
        "https://portal.sisbr.coop.br/rsa/risco - modal Opcoes de Impressao",
        "",
        "By.XPATH",
        "",
        "Print 6.",
    ),
    (
        13,
        "Screen_RsaModalImpressao",
        "OPCAO_FORMATO_XLSX",
        "opcao XLSX no select de formato",
        "Selecionar o formato XLSX",
        "https://portal.sisbr.coop.br/rsa/risco - modal Opcoes de Impressao",
        "",
        "By.XPATH",
        "",
        "Print 6.",
    ),
    (
        14,
        "Screen_RsaModalImpressao",
        "BTN_GERAR_RELATORIO",
        "botao Gerar Relatorio no modal",
        "Gerar o relatorio na lista de disponiveis",
        "https://portal.sisbr.coop.br/rsa/risco - modal Opcoes de Impressao",
        "",
        "By.XPATH",
        "",
        "Print 6.",
    ),
    (
        15,
        "Screen_RsaRelatoriosDisponiveis",
        "VALIDACAO_RELATORIOS_DISPONIVEIS",
        "titulo ou container da tela Relatorios Disponiveis",
        "Validar que a listagem de relatorios foi aberta",
        "https://portal.sisbr.coop.br/rsa/risco - painel Relatorios Disponiveis",
        "",
        "By.XPATH",
        "",
        "Print 7.",
    ),
    (
        16,
        "Screen_RsaRelatoriosDisponiveis",
        "TABELA_RELATORIOS",
        "tabela de relatorios gerados",
        "Localizar a tabela de relatorios",
        "https://portal.sisbr.coop.br/rsa/risco - painel Relatorios Disponiveis",
        "",
        "By.XPATH",
        "",
        "Print 7.",
    ),
    (
        17,
        "Screen_RsaRelatoriosDisponiveis",
        "LINHA_RELATORIO_TEMPLATE",
        "linha do relatorio desejado com filtros dinamicos",
        "Encontrar a linha do relatorio correto",
        "https://portal.sisbr.coop.br/rsa/risco - painel Relatorios Disponiveis",
        "",
        "By.XPATH",
        "",
        "Print 7. Ideal para combinar relatorio e situacao.",
    ),
    (
        18,
        "Screen_RsaRelatoriosDisponiveis",
        "BTN_IMPRIMIR_TEMPLATE",
        "botao imprimir na linha do relatorio desejado",
        "Baixar o arquivo da linha selecionada",
        "https://portal.sisbr.coop.br/rsa/risco - painel Relatorios Disponiveis",
        "",
        "By.XPATH",
        "",
        "Print 7.",
    ),
]


def _autosize(worksheet) -> None:
    for column_cells in worksheet.columns:
        values = [str(cell.value or "") for cell in column_cells]
        worksheet.column_dimensions[column_cells[0].column_letter].width = min(
            max(len(value) for value in values) + 2,
            80,
        )


def build_workbook() -> Workbook:
    workbook = Workbook()

    instructions = workbook.active
    instructions.title = "Instrucoes"
    instructions["A1"] = "Como preencher"
    instructions["A1"].font = Font(bold=True)
    instructions["A2"] = "Preencha OuterHTML e, se souber, o seletor final."
    instructions["A3"] = "O acesso ao modulo RSA vem da lib_sisbr_desktop; esta planilha lista apenas seletores web."
    instructions["A4"] = "Se preferir, deixe apenas OuterHTML que a derivacao do seletor pode ser feita depois."
    instructions["A5"] = "Os recortes dos elementos estao em Prints_telas/Recortes_Seletores com o nome do seletor."
    instructions["A6"] = "Use a aba Seletores como fonte unica dos campos pendentes do selectors_config.py."
    instructions.column_dimensions["A"].width = 120

    selectors = workbook.create_sheet("Seletores")
    selectors.append(HEADERS)
    for cell in selectors[1]:
        cell.font = Font(bold=True)

    for row in ROWS:
        selectors.append(row)

    selectors.freeze_panes = "A2"
    _autosize(selectors)
    return workbook


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    workbook = build_workbook()
    workbook.save(OUTPUT)
    print(f"Arquivo gerado em: {OUTPUT}")


if __name__ == "__main__":
    main()
