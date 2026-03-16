from pathlib import Path

from rsac_relatorios_risco.web import rpa_actions
from rsac_relatorios_risco.web import selectors_config
from rsac_relatorios_risco.web.rsa_portal_stub import RsaPortalNotReadyError


class RsaPortalPendingSelectorError(RsaPortalNotReadyError):
    pass


class RsaPortalFlow:
    def __init__(self, driver, actions=rpa_actions, selectors_module=selectors_config) -> None:
        self.driver = driver
        self.actions = actions
        self.selectors = selectors_module

    def abrir_modulo_rsa(self) -> None:
        screen = self.selectors.Screen_Sisbr
        home = self.selectors.Screen_RsaHome
        self._ensure_ready("BTN_MODULO_RSA", screen.BTN_MODULO_RSA)
        self._ensure_ready("VALIDACAO_HOME", home.VALIDACAO_HOME)
        self.actions.click(
            self.driver,
            screen.BTN_MODULO_RSA,
            screen.BTN_MODULO_RSA_TIPO,
            verify_selector=home.VALIDACAO_HOME,
            verify_type=home.VALIDACAO_HOME_TIPO,
        )

    def preencher_filtros(self, *, competencia: str, tipo_relatorio: str) -> None:
        screen = self.selectors.Screen_RsaFiltros
        self._ensure_ready("INPUT_COMPETENCIA", screen.INPUT_COMPETENCIA)
        self._ensure_ready("INPUT_TIPO_RELATORIO", screen.INPUT_TIPO_RELATORIO)
        self._ensure_ready("BTN_APLICAR_FILTROS", screen.BTN_APLICAR_FILTROS)

        self.actions.type_into(
            self.driver,
            screen.INPUT_COMPETENCIA,
            competencia,
            screen.INPUT_COMPETENCIA_TIPO,
            verify_text=True,
        )
        self.actions.type_into(
            self.driver,
            screen.INPUT_TIPO_RELATORIO,
            tipo_relatorio,
            screen.INPUT_TIPO_RELATORIO_TIPO,
            verify_text=True,
        )
        self.actions.click(
            self.driver,
            screen.BTN_APLICAR_FILTROS,
            screen.BTN_APLICAR_FILTROS_TIPO,
        )

    def selecionar_cooperativas(self, cooperativas: list[str]) -> None:
        screen = self.selectors.Screen_RsaFiltros
        self._ensure_ready(
            "BTN_SELECIONAR_COOPERATIVAS",
            screen.BTN_SELECIONAR_COOPERATIVAS,
        )
        self._ensure_ready("INPUT_BUSCA_COOPERATIVA", screen.INPUT_BUSCA_COOPERATIVA)
        self._ensure_ready(
            "OPCAO_COOPERATIVA_TEMPLATE",
            screen.OPCAO_COOPERATIVA_TEMPLATE,
        )

        self.actions.click(
            self.driver,
            screen.BTN_SELECIONAR_COOPERATIVAS,
            screen.BTN_SELECIONAR_COOPERATIVAS_TIPO,
        )
        for cooperativa in cooperativas:
            self.actions.type_into(
                self.driver,
                screen.INPUT_BUSCA_COOPERATIVA,
                cooperativa,
                screen.INPUT_BUSCA_COOPERATIVA_TIPO,
                verify_text=True,
            )
            selector = screen.OPCAO_COOPERATIVA_TEMPLATE.format(
                cooperativa=cooperativa,
            )
            self.actions.click(
                self.driver,
                selector,
                screen.OPCAO_COOPERATIVA_TEMPLATE_TIPO,
            )

    def exportar_relatorio(self, download_dir: Path) -> Path:
        screen = self.selectors.Screen_RsaExportacao
        self._ensure_ready("BTN_EXPORTAR", screen.BTN_EXPORTAR)
        self._ensure_ready("VALIDACAO_EXPORTACAO", screen.VALIDACAO_EXPORTACAO)
        self.actions.click(
            self.driver,
            screen.BTN_EXPORTAR,
            screen.BTN_EXPORTAR_TIPO,
            verify_selector=screen.VALIDACAO_EXPORTACAO,
            verify_type=screen.VALIDACAO_EXPORTACAO_TIPO,
        )
        return download_dir

    def _ensure_ready(self, field_name: str, value: str) -> None:
        if self.selectors.is_pending_selector(value):
            raise RsaPortalPendingSelectorError(
                f"Seletor pendente: {field_name}. Preencha em selectors_config.py antes de usar o fluxo web.",
            )
