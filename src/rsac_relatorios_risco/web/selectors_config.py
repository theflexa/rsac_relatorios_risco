"""
Seletores do fluxo RSA organizados por etapa da jornada web.

Os valores nascem com placeholders explicitos para preenchimento posterior.
Quando um seletor ainda nao foi mapeado, o fluxo deve falhar com erro claro.
"""

try:
    from selenium.webdriver.common.by import By  # type: ignore
except ImportError:  # pragma: no cover - fallback local para manter o contrato sem Selenium instalado
    class By:  # noqa: N801
        XPATH = "xpath"
        CSS_SELECTOR = "css selector"
        ID = "id"
        NAME = "name"


PENDING_SELECTOR_PREFIX = "__PREENCHER__:"


def is_pending_selector(value: str) -> bool:
    return isinstance(value, str) and value.startswith(PENDING_SELECTOR_PREFIX)


class Screen_RsaHome:
    VALIDACAO_HOME = (
        "//div[contains(@class,'ss-toolbar-item')][.//span[contains(normalize-space(),'Relat')]]"
    )
    VALIDACAO_HOME_TIPO = By.XPATH

    BTN_MENU_RELATORIOS = VALIDACAO_HOME
    BTN_MENU_RELATORIOS_TIPO = By.XPATH


class Screen_RsaBrowser:
    TITULO_CONTEM = (
        "RSAC",
        "Riscos Social",
        "Climatico",
        "Climático",
    )
    URL_CONTEM = (
        "rsac",
        "risco",
        "social",
        "ambiental",
        "climatico",
        "clim%C3%A1tico",
    )


class Screen_RsaLogin:
    VALIDACAO_LOGIN = "username"
    VALIDACAO_LOGIN_TIPO = By.ID

    INPUT_LOGIN = "username"
    INPUT_LOGIN_TIPO = By.ID

    INPUT_SENHA = "password"
    INPUT_SENHA_TIPO = By.ID

    BTN_LOGAR = "kc-login"
    BTN_LOGAR_TIPO = By.ID


class Screen_RsaMenuRelatorios:
    ITEM_RELATORIOS_RSAC = (
        "//a[contains(@class,'ss-navbar-title') and contains(normalize-space(),'Riscos Social') and contains(normalize-space(),'Clim')]"
    )
    ITEM_RELATORIOS_RSAC_TIPO = By.XPATH


class Screen_RsaFormulario:
    VALIDACAO_TELA_FORMULARIO = "//button[@type='button' and @value='Exportar']"
    VALIDACAO_TELA_FORMULARIO_TIPO = By.XPATH

    SELECT_TIPO_RELATORIO = "tipo-relatorio"
    SELECT_TIPO_RELATORIO_TIPO = By.ID

    OPCAO_TIPO_RELATORIO_RELATORIO_POR_COOPERATIVA = (
        "//div[@role='option']//span[contains(@class,'ng-option-label') and contains(normalize-space(),'Cooperativa')]"
    )
    OPCAO_TIPO_RELATORIO_RELATORIO_POR_COOPERATIVA_TIPO = By.XPATH

    SELECT_SINGULAR = "combo-singular"
    SELECT_SINGULAR_TIPO = By.ID

    OPCAO_SINGULAR_TEMPLATE = (
        "//div[@role='option']//span[contains(@class,'ng-option-label') and starts-with(normalize-space(), '{cooperativa} -')]"
    )
    OPCAO_SINGULAR_TEMPLATE_TIPO = By.XPATH

    INPUT_MES_ANO = "mes-ano"
    INPUT_MES_ANO_TIPO = By.ID

    BTN_EXPORTAR = "//button[@type='button' and @value='Exportar']"
    BTN_EXPORTAR_TIPO = By.XPATH


class Screen_RsaModalImpressao:
    MODAL_OPCOES_IMPRESSAO = (
        "//h6[contains(normalize-space(),'Op') and contains(normalize-space(),'Impress')]"
    )
    MODAL_OPCOES_IMPRESSAO_TIPO = By.XPATH

    SELECT_FORMATO = "formato-impressao"
    SELECT_FORMATO_TIPO = By.ID

    OPCAO_FORMATO_XLSX = (
        "//div[@role='option']//span[contains(@class,'ng-option-label') and normalize-space()='XLSX']"
    )
    OPCAO_FORMATO_XLSX_TIPO = By.XPATH

    BTN_GERAR_RELATORIO = (
        "//button[@type='button'][.//span[contains(normalize-space(),'Gerar') and contains(normalize-space(),'Relat')]]"
    )
    BTN_GERAR_RELATORIO_TIPO = By.XPATH


class Screen_RsaRelatoriosDisponiveis:
    VALIDACAO_RELATORIOS_DISPONIVEIS = (
        "//h6[contains(normalize-space(),'Relat') and contains(normalize-space(),'Dispon')]"
    )
    VALIDACAO_RELATORIOS_DISPONIVEIS_TIPO = By.XPATH

    TABELA_RELATORIOS = "//table[@aria-label='Tabela de Resultados']"
    TABELA_RELATORIOS_TIPO = By.XPATH

    LINHA_RELATORIO_TEMPLATE = (
        "//table[@aria-label='Tabela de Resultados']//tr["
        "td[1][contains(normalize-space(), '{situacao}')] and "
        "td[2][contains(normalize-space(), '{relatorio}')] and "
        "td[5][contains(normalize-space(), '{tipo}')]]"
    )
    LINHA_RELATORIO_TEMPLATE_TIPO = By.XPATH

    BTN_IMPRIMIR_TEMPLATE = (
        "//table[@aria-label='Tabela de Resultados']//tr["
        "td[1][contains(normalize-space(), '{situacao}')] and "
        "td[2][contains(normalize-space(), '{relatorio}')] and "
        "td[5][contains(normalize-space(), '{tipo}')]]//a[@title='Imprimir Arquivo']"
    )
    BTN_IMPRIMIR_TEMPLATE_TIPO = By.XPATH


class Screen_RsaFiltros:
    """
    Compatibilidade temporaria com o scaffold anterior.

    O fluxo real sera migrado para Screen_RsaFormulario.
    """

    INPUT_COMPETENCIA = Screen_RsaFormulario.INPUT_MES_ANO
    INPUT_COMPETENCIA_TIPO = Screen_RsaFormulario.INPUT_MES_ANO_TIPO

    INPUT_TIPO_RELATORIO = "//*[@id='tipo-relatorio']//input"
    INPUT_TIPO_RELATORIO_TIPO = By.XPATH

    BTN_SELECIONAR_COOPERATIVAS = Screen_RsaFormulario.SELECT_SINGULAR
    BTN_SELECIONAR_COOPERATIVAS_TIPO = Screen_RsaFormulario.SELECT_SINGULAR_TIPO

    INPUT_BUSCA_COOPERATIVA = "//*[@id='combo-singular']//input"
    INPUT_BUSCA_COOPERATIVA_TIPO = By.XPATH

    OPCAO_COOPERATIVA_TEMPLATE = Screen_RsaFormulario.OPCAO_SINGULAR_TEMPLATE
    OPCAO_COOPERATIVA_TEMPLATE_TIPO = Screen_RsaFormulario.OPCAO_SINGULAR_TEMPLATE_TIPO

    BTN_APLICAR_FILTROS = Screen_RsaFormulario.BTN_EXPORTAR
    BTN_APLICAR_FILTROS_TIPO = Screen_RsaFormulario.BTN_EXPORTAR_TIPO


class Screen_RsaExportacao:
    """
    Compatibilidade temporaria com o scaffold anterior.

    O fluxo real sera migrado para Screen_RsaModalImpressao e Screen_RsaRelatoriosDisponiveis.
    """

    BTN_EXPORTAR = Screen_RsaModalImpressao.BTN_GERAR_RELATORIO
    BTN_EXPORTAR_TIPO = Screen_RsaModalImpressao.BTN_GERAR_RELATORIO_TIPO

    VALIDACAO_EXPORTACAO = Screen_RsaRelatoriosDisponiveis.VALIDACAO_RELATORIOS_DISPONIVEIS
    VALIDACAO_EXPORTACAO_TIPO = Screen_RsaRelatoriosDisponiveis.VALIDACAO_RELATORIOS_DISPONIVEIS_TIPO
