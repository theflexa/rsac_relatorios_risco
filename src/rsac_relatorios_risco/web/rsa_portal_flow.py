from pathlib import Path
import os
import unicodedata

from utils import rpa_actions
from rsac_relatorios_risco.web import selectors_config
from rsac_relatorios_risco.web.rsa_portal_stub import RsaPortalNotReadyError
from rsac_relatorios_risco.windows.save_as_flow import WindowsSaveAsFlow


class RsaPortalPendingSelectorError(RsaPortalNotReadyError):
    pass


class RsaPortalAuthenticationError(RsaPortalNotReadyError):
    pass


class RsaPortalFlow:
    RSA_RISCO_URL = "https://portal.sisbr.coop.br/rsa/risco"

    def __init__(
        self,
        driver,
        actions=rpa_actions,
        save_as_flow=None,
        selectors_module=selectors_config,
    ) -> None:
        self.driver = driver
        self.actions = actions
        self.save_as_flow = save_as_flow or WindowsSaveAsFlow()
        self.selectors = selectors_module
        self._current_competencia: str | None = None
        self._current_cooperativa: str | None = None

    def validar_home(self) -> None:
        self._ensure_browser_context()
        logged_in_now = self._login_if_needed()
        home = self.selectors.Screen_RsaHome
        self._ensure_ready("VALIDACAO_HOME", home.VALIDACAO_HOME)
        self.actions.wait_element(
            self.driver,
            home.VALIDACAO_HOME,
            home.VALIDACAO_HOME_TIPO,
            timeout=30 if logged_in_now else 10,
        )

    def abrir_menu_relatorios(self) -> None:
        home = self.selectors.Screen_RsaHome
        self._ensure_ready("BTN_MENU_RELATORIOS", home.BTN_MENU_RELATORIOS)
        self.actions.click(
            self.driver,
            home.BTN_MENU_RELATORIOS,
            home.BTN_MENU_RELATORIOS_TIPO,
        )

    def abrir_relatorio_rsac(self) -> None:
        menu = self.selectors.Screen_RsaMenuRelatorios
        formulario = self.selectors.Screen_RsaFormulario
        self._ensure_ready("ITEM_RELATORIOS_RSAC", menu.ITEM_RELATORIOS_RSAC)
        self._ensure_ready(
            "VALIDACAO_TELA_FORMULARIO",
            formulario.VALIDACAO_TELA_FORMULARIO,
        )
        try:
            self.actions.click(
                self.driver,
                menu.ITEM_RELATORIOS_RSAC,
                menu.ITEM_RELATORIOS_RSAC_TIPO,
                verify_selector=formulario.VALIDACAO_TELA_FORMULARIO,
                verify_type=formulario.VALIDACAO_TELA_FORMULARIO_TIPO,
            )
        except Exception:
            self.driver.get(self.RSA_RISCO_URL)
            self.actions.wait_element(
                self.driver,
                formulario.VALIDACAO_TELA_FORMULARIO,
                formulario.VALIDACAO_TELA_FORMULARIO_TIPO,
                condition="present",
                timeout=40,
            )

    def preencher_formulario(self, *, competencia: str, cooperativa: str) -> None:
        screen = self.selectors.Screen_RsaFormulario
        self._ensure_ready("INPUT_MES_ANO", screen.INPUT_MES_ANO)
        self._ensure_ready("SELECT_TIPO_RELATORIO", screen.SELECT_TIPO_RELATORIO)
        self._ensure_ready(
            "OPCAO_TIPO_RELATORIO_RELATORIO_POR_COOPERATIVA",
            screen.OPCAO_TIPO_RELATORIO_RELATORIO_POR_COOPERATIVA,
        )
        self._ensure_ready("SELECT_SINGULAR", screen.SELECT_SINGULAR)
        self._ensure_ready("OPCAO_SINGULAR_TEMPLATE", screen.OPCAO_SINGULAR_TEMPLATE)

        self.actions.type_into(
            self.driver,
            screen.INPUT_MES_ANO,
            competencia,
            screen.INPUT_MES_ANO_TIPO,
            verify_text=True,
        )
        self.actions.click(
            self.driver,
            screen.SELECT_TIPO_RELATORIO,
            screen.SELECT_TIPO_RELATORIO_TIPO,
        )
        self.actions.click(
            self.driver,
            screen.OPCAO_TIPO_RELATORIO_RELATORIO_POR_COOPERATIVA,
            screen.OPCAO_TIPO_RELATORIO_RELATORIO_POR_COOPERATIVA_TIPO,
        )
        self.actions.click(
            self.driver,
            screen.SELECT_SINGULAR,
            screen.SELECT_SINGULAR_TIPO,
        )
        opcao_cooperativa = screen.OPCAO_SINGULAR_TEMPLATE.format(
            cooperativa=cooperativa,
        )
        self.actions.click(
            self.driver,
            opcao_cooperativa,
            screen.OPCAO_SINGULAR_TEMPLATE_TIPO,
        )
        self._current_competencia = competencia
        self._current_cooperativa = cooperativa

    def abrir_modal_exportacao(self) -> None:
        formulario = self.selectors.Screen_RsaFormulario
        modal = self.selectors.Screen_RsaModalImpressao
        self._ensure_ready("BTN_EXPORTAR", formulario.BTN_EXPORTAR)
        self._ensure_ready("MODAL_OPCOES_IMPRESSAO", modal.MODAL_OPCOES_IMPRESSAO)
        self.actions.click(
            self.driver,
            formulario.BTN_EXPORTAR,
            formulario.BTN_EXPORTAR_TIPO,
            verify_selector=modal.MODAL_OPCOES_IMPRESSAO,
            verify_type=modal.MODAL_OPCOES_IMPRESSAO_TIPO,
        )

    def selecionar_formato_xlsx(self) -> None:
        modal = self.selectors.Screen_RsaModalImpressao
        self._ensure_ready("SELECT_FORMATO", modal.SELECT_FORMATO)
        self._ensure_ready("OPCAO_FORMATO_XLSX", modal.OPCAO_FORMATO_XLSX)
        self.actions.click(
            self.driver,
            modal.SELECT_FORMATO,
            modal.SELECT_FORMATO_TIPO,
        )
        self.actions.click(
            self.driver,
            modal.OPCAO_FORMATO_XLSX,
            modal.OPCAO_FORMATO_XLSX_TIPO,
        )

    def gerar_relatorio(self) -> None:
        modal = self.selectors.Screen_RsaModalImpressao
        disponiveis = self.selectors.Screen_RsaRelatoriosDisponiveis
        self._ensure_ready("BTN_GERAR_RELATORIO", modal.BTN_GERAR_RELATORIO)
        self._ensure_ready(
            "VALIDACAO_RELATORIOS_DISPONIVEIS",
            disponiveis.VALIDACAO_RELATORIOS_DISPONIVEIS,
        )
        self.actions.click(
            self.driver,
            modal.BTN_GERAR_RELATORIO,
            modal.BTN_GERAR_RELATORIO_TIPO,
            verify_selector=disponiveis.VALIDACAO_RELATORIOS_DISPONIVEIS,
            verify_type=disponiveis.VALIDACAO_RELATORIOS_DISPONIVEIS_TIPO,
        )

    def abrir_relatorio_disponivel(
        self,
        *,
        download_dir: Path,
        relatorio: str = "RELATORIO_RISCO_COOPERATIVA",
        situacao: str = "Processado com sucesso",
        tipo: str = "XLSX",
    ) -> Path:
        screen = self.selectors.Screen_RsaRelatoriosDisponiveis
        self._ensure_ready("TABELA_RELATORIOS", screen.TABELA_RELATORIOS)
        self._ensure_ready("BTN_IMPRIMIR_TEMPLATE", screen.BTN_IMPRIMIR_TEMPLATE)

        self.actions.wait_element(
            self.driver,
            screen.TABELA_RELATORIOS,
            screen.TABELA_RELATORIOS_TIPO,
        )
        self._validar_titulo_relatorio(relatorio=relatorio)
        botao_imprimir = screen.BTN_IMPRIMIR_TEMPLATE.format(
            relatorio=relatorio,
            situacao=situacao,
            tipo=tipo,
        )
        self.actions.click(
            self.driver,
            botao_imprimir,
            screen.BTN_IMPRIMIR_TEMPLATE_TIPO,
        )
        return self.save_as_flow.save_file(self._build_download_path(download_dir))

    def _validar_titulo_relatorio(self, *, relatorio: str) -> None:
        titulo_xpath = (
            "//table[@aria-label='Tabela de Resultados']"
            f"//tr/td[2][normalize-space()='{relatorio}']"
        )
        try:
            self.actions.wait_element(
                self.driver,
                titulo_xpath,
                "xpath",
                timeout=10,
            )
        except Exception:
            all_titles_xpath = (
                "//table[@aria-label='Tabela de Resultados']//tr/td[2]"
            )
            cells = self.driver.find_elements("xpath", all_titles_xpath)
            titulos = [c.text.strip() for c in cells if c.text.strip()]
            raise RuntimeError(
                f"Titulo de relatorio esperado: {relatorio!r}. "
                f"Titulos encontrados: {titulos!r}"
            ) from None

    def executar_fluxo_exportacao(
        self,
        *,
        competencia: str,
        cooperativa: str,
        download_dir: Path,
        relatorio: str = "RELATORIO_RISCO_COOPERATIVA",
        situacao: str = "Processado com sucesso",
        tipo: str = "XLSX",
    ) -> Path:
        self.validar_home()
        self.abrir_menu_relatorios()
        self.abrir_relatorio_rsac()
        self.preencher_formulario(
            competencia=competencia,
            cooperativa=cooperativa,
        )
        self.abrir_modal_exportacao()
        self.selecionar_formato_xlsx()
        self.gerar_relatorio()
        return self.abrir_relatorio_disponivel(
            download_dir=download_dir,
            relatorio=relatorio,
            situacao=situacao,
            tipo=tipo,
        )

    def preencher_filtros(self, *, competencia: str, tipo_relatorio: str) -> None:
        del tipo_relatorio
        self.abrir_menu_relatorios()
        self.abrir_relatorio_rsac()
        self._ensure_ready("INPUT_MES_ANO", self.selectors.Screen_RsaFormulario.INPUT_MES_ANO)
        self._ensure_ready(
            "SELECT_TIPO_RELATORIO",
            self.selectors.Screen_RsaFormulario.SELECT_TIPO_RELATORIO,
        )
        self._ensure_ready(
            "OPCAO_TIPO_RELATORIO_RELATORIO_POR_COOPERATIVA",
            self.selectors.Screen_RsaFormulario.OPCAO_TIPO_RELATORIO_RELATORIO_POR_COOPERATIVA,
        )
        self.actions.type_into(
            self.driver,
            self.selectors.Screen_RsaFormulario.INPUT_MES_ANO,
            competencia,
            self.selectors.Screen_RsaFormulario.INPUT_MES_ANO_TIPO,
            verify_text=True,
        )
        self._current_competencia = competencia
        self.actions.click(
            self.driver,
            self.selectors.Screen_RsaFormulario.SELECT_TIPO_RELATORIO,
            self.selectors.Screen_RsaFormulario.SELECT_TIPO_RELATORIO_TIPO,
        )
        self.actions.click(
            self.driver,
            self.selectors.Screen_RsaFormulario.OPCAO_TIPO_RELATORIO_RELATORIO_POR_COOPERATIVA,
            self.selectors.Screen_RsaFormulario.OPCAO_TIPO_RELATORIO_RELATORIO_POR_COOPERATIVA_TIPO,
        )

    def selecionar_cooperativas(self, cooperativas: list[str]) -> None:
        if not cooperativas:
            return
        cooperativa = cooperativas[0]
        screen = self.selectors.Screen_RsaFormulario
        self._ensure_ready("SELECT_SINGULAR", screen.SELECT_SINGULAR)
        self._ensure_ready("OPCAO_SINGULAR_TEMPLATE", screen.OPCAO_SINGULAR_TEMPLATE)
        self.actions.click(
            self.driver,
            screen.SELECT_SINGULAR,
            screen.SELECT_SINGULAR_TIPO,
        )
        self.actions.click(
            self.driver,
            screen.OPCAO_SINGULAR_TEMPLATE.format(cooperativa=cooperativa),
            screen.OPCAO_SINGULAR_TEMPLATE_TIPO,
        )
        self._current_cooperativa = cooperativa

    def exportar_relatorio(self, download_dir: Path) -> Path:
        self.abrir_modal_exportacao()
        self.selecionar_formato_xlsx()
        self.gerar_relatorio()
        return self.abrir_relatorio_disponivel(download_dir=download_dir)

    def _ensure_ready(self, field_name: str, value: str) -> None:
        if self.selectors.is_pending_selector(value):
            raise RsaPortalPendingSelectorError(
                f"Seletor pendente: {field_name}. Preencha em selectors_config.py antes de usar o fluxo web.",
            )

    def _build_download_path(self, download_dir: Path) -> Path:
        cooperativa = self._current_cooperativa or "coop"
        competencia = (self._current_competencia or "000000").replace("/", "")
        return Path(download_dir) / f"relatorio_{cooperativa}_{competencia}.xlsx"

    def _ensure_browser_context(self) -> None:
        handles = list(getattr(self.driver, "window_handles", []) or [])
        if not handles:
            return

        current_handle = getattr(self.driver, "current_window_handle", None)
        ordered_handles = self._ordered_handles(handles, current_handle)

        for handle in ordered_handles:
            self.driver.switch_to.window(handle)
            if self._is_rsac_context():
                return

        if current_handle:
            self.driver.switch_to.window(current_handle)

    @staticmethod
    def _ordered_handles(handles: list[str], current_handle: str | None) -> list[str]:
        if current_handle and current_handle in handles:
            return [current_handle, *[handle for handle in handles if handle != current_handle]]
        return handles

    def _is_rsac_context(self) -> bool:
        browser = getattr(self.selectors, "Screen_RsaBrowser", None)
        if browser is None:
            return False

        current_title = self._normalize_text(getattr(self.driver, "title", ""))
        current_url = self._normalize_text(getattr(self.driver, "current_url", ""))

        title_keywords = tuple(self._normalize_text(value) for value in getattr(browser, "TITULO_CONTEM", ()))
        url_keywords = tuple(self._normalize_text(value) for value in getattr(browser, "URL_CONTEM", ()))

        title_match = any(keyword and keyword in current_title for keyword in title_keywords)
        url_match = any(keyword and keyword in current_url for keyword in url_keywords)
        return title_match or url_match

    def _login_if_needed(self) -> bool:
        login_screen = getattr(self.selectors, "Screen_RsaLogin", None)
        if login_screen is None or not self._is_login_context():
            return False

        login_user = os.getenv("LOGIN_USER") or os.getenv("USUARIO")
        login_password = os.getenv("LOGIN_PASSWORD") or os.getenv("SENHA")
        if not login_user or not login_password:
            raise RsaPortalAuthenticationError(
                "Tela de login RSA detectada, mas LOGIN_USER/LOGIN_PASSWORD nao estao configurados no .env.",
            )

        self.actions.type_into(
            self.driver,
            login_screen.INPUT_LOGIN,
            login_user,
            login_screen.INPUT_LOGIN_TIPO,
            verify_text=True,
        )
        self.actions.type_into(
            self.driver,
            login_screen.INPUT_SENHA,
            login_password,
            login_screen.INPUT_SENHA_TIPO,
            verify_text=False,
        )
        self.actions.click(
            self.driver,
            login_screen.BTN_LOGAR,
            login_screen.BTN_LOGAR_TIPO,
        )
        return True

    def _is_login_context(self) -> bool:
        title = self._normalize_text(getattr(self.driver, "title", ""))
        url = self._normalize_text(getattr(self.driver, "current_url", ""))
        return "login sisbr" in title or "/auth/realms/sisbr/" in url

    @staticmethod
    def _normalize_text(value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value or "")
        ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
        return ascii_only.casefold()
