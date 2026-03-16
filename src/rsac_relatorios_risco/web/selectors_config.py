"""
Seletores do fluxo RSA organizados por tela.

Os valores nascem com placeholders explícitos para preenchimento posterior.
Quando um seletor ainda não foi mapeado, o fluxo deve falhar com erro claro.
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


class Screen_Sisbr:
    BTN_MODULO_RSA = "__PREENCHER__: botão/atalho para abrir o módulo RSA"
    BTN_MODULO_RSA_TIPO = By.XPATH


class Screen_RsaHome:
    VALIDACAO_HOME = "__PREENCHER__: elemento de validação da home RSA"
    VALIDACAO_HOME_TIPO = By.XPATH


class Screen_RsaFiltros:
    INPUT_COMPETENCIA = "__PREENCHER__: campo da competência"
    INPUT_COMPETENCIA_TIPO = By.XPATH

    INPUT_TIPO_RELATORIO = "__PREENCHER__: campo ou combo do tipo de relatório"
    INPUT_TIPO_RELATORIO_TIPO = By.XPATH

    BTN_SELECIONAR_COOPERATIVAS = "__PREENCHER__: botão para abrir seleção de cooperativas"
    BTN_SELECIONAR_COOPERATIVAS_TIPO = By.XPATH

    INPUT_BUSCA_COOPERATIVA = "__PREENCHER__: campo de busca da cooperativa"
    INPUT_BUSCA_COOPERATIVA_TIPO = By.XPATH

    OPCAO_COOPERATIVA_TEMPLATE = "__PREENCHER__: template da opção de cooperativa com {cooperativa}"
    OPCAO_COOPERATIVA_TEMPLATE_TIPO = By.XPATH

    BTN_APLICAR_FILTROS = "__PREENCHER__: botão aplicar/consultar filtros"
    BTN_APLICAR_FILTROS_TIPO = By.XPATH


class Screen_RsaExportacao:
    BTN_EXPORTAR = "__PREENCHER__: botão exportar relatório"
    BTN_EXPORTAR_TIPO = By.XPATH

    VALIDACAO_EXPORTACAO = "__PREENCHER__: elemento de validação da exportação"
    VALIDACAO_EXPORTACAO_TIPO = By.XPATH
