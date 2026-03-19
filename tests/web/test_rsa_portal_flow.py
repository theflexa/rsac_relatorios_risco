from pathlib import Path
from types import SimpleNamespace

import pytest

from rsac_relatorios_risco.web.rsa_portal_flow import (
    RsaPortalFlow,
    RsaPortalPendingSelectorError,
)


class FakeActions:
    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def click(self, driver, selector, selector_type, **kwargs):
        self.calls.append(("click", selector, selector_type, kwargs))
        return True

    def type_into(self, driver, selector, text, selector_type, **kwargs):
        self.calls.append(("type_into", selector, text, selector_type, kwargs))
        return True

    def wait_element(self, driver, selector, selector_type, **kwargs):
        self.calls.append(("wait_element", selector, selector_type, kwargs))
        return True


class FakeSaveAsFlow:
    def __init__(self) -> None:
        self.calls: list[Path] = []

    def save_file(self, destination_path: Path) -> Path:
        self.calls.append(destination_path)
        return destination_path


def _resolved_selectors():
    return SimpleNamespace(
        Screen_RsaHome=SimpleNamespace(
            VALIDACAO_HOME="//div[@id='home-rsa']",
            VALIDACAO_HOME_TIPO="xpath",
            BTN_MENU_RELATORIOS="//button[@id='menu-relatorios']",
            BTN_MENU_RELATORIOS_TIPO="xpath",
        ),
        Screen_RsaMenuRelatorios=SimpleNamespace(
            ITEM_RELATORIOS_RSAC="//a[@id='menu-rsac']",
            ITEM_RELATORIOS_RSAC_TIPO="xpath",
        ),
        Screen_RsaFormulario=SimpleNamespace(
            VALIDACAO_TELA_FORMULARIO="//h6[@id='titulo-rsac']",
            VALIDACAO_TELA_FORMULARIO_TIPO="xpath",
            SELECT_TIPO_RELATORIO="tipo-relatorio",
            SELECT_TIPO_RELATORIO_TIPO="id",
            OPCAO_TIPO_RELATORIO_RELATORIO_POR_COOPERATIVA="//span[.='Relatorio por Cooperativa']",
            OPCAO_TIPO_RELATORIO_RELATORIO_POR_COOPERATIVA_TIPO="xpath",
            SELECT_SINGULAR="combo-singular",
            SELECT_SINGULAR_TIPO="id",
            OPCAO_SINGULAR_TEMPLATE="//span[starts-with(normalize-space(), '{cooperativa} -')]",
            OPCAO_SINGULAR_TEMPLATE_TIPO="xpath",
            INPUT_MES_ANO="mes-ano",
            INPUT_MES_ANO_TIPO="id",
            BTN_EXPORTAR="//button[@value='Exportar']",
            BTN_EXPORTAR_TIPO="xpath",
        ),
        Screen_RsaModalImpressao=SimpleNamespace(
            MODAL_OPCOES_IMPRESSAO="//h6[.='Opcoes de Impressao']",
            MODAL_OPCOES_IMPRESSAO_TIPO="xpath",
            SELECT_FORMATO="formato-impressao",
            SELECT_FORMATO_TIPO="id",
            OPCAO_FORMATO_XLSX="//span[.='XLSX']",
            OPCAO_FORMATO_XLSX_TIPO="xpath",
            BTN_GERAR_RELATORIO="//button[@value='Gerar Relatorio']",
            BTN_GERAR_RELATORIO_TIPO="xpath",
        ),
        Screen_RsaRelatoriosDisponiveis=SimpleNamespace(
            VALIDACAO_RELATORIOS_DISPONIVEIS="//h6[.='Relatorios Disponiveis']",
            VALIDACAO_RELATORIOS_DISPONIVEIS_TIPO="xpath",
            TABELA_RELATORIOS="//table[@aria-label='Tabela de Resultados']",
            TABELA_RELATORIOS_TIPO="xpath",
            LINHA_RELATORIO_TEMPLATE="//tr[td[1][contains(., '{situacao}')] and td[2][contains(., '{relatorio}')] and td[5][contains(., '{tipo}')]]",
            LINHA_RELATORIO_TEMPLATE_TIPO="xpath",
            BTN_IMPRIMIR_TEMPLATE="//tr[td[1][contains(., '{situacao}')] and td[2][contains(., '{relatorio}')] and td[5][contains(., '{tipo}')]]//a[@title='Imprimir Arquivo']",
            BTN_IMPRIMIR_TEMPLATE_TIPO="xpath",
        ),
        is_pending_selector=lambda value: isinstance(value, str) and value.startswith("__PREENCHER__:"),
    )


def test_flow_raises_clear_error_when_selector_is_still_pending():
    selectors = _resolved_selectors()
    formulario = dict(selectors.Screen_RsaFormulario.__dict__)
    formulario["INPUT_MES_ANO"] = "__PREENCHER__: campo mes-ano"
    selectors.Screen_RsaFormulario = SimpleNamespace(**formulario)
    flow = RsaPortalFlow(
        driver=object(),
        actions=FakeActions(),
        selectors_module=selectors,
    )

    with pytest.raises(RsaPortalPendingSelectorError, match="INPUT_MES_ANO"):
        flow.preencher_formulario(competencia="03/2026", cooperativa="3333")


def test_flow_validates_home_when_selector_is_ready():
    actions = FakeActions()
    flow = RsaPortalFlow(
        driver=object(),
        actions=actions,
        selectors_module=_resolved_selectors(),
    )

    flow.validar_home()

    assert actions.calls == [
        ("wait_element", "//div[@id='home-rsa']", "xpath", {}),
    ]


def test_flow_executes_real_rsa_sequence_when_selectors_are_ready(tmp_path: Path):
    actions = FakeActions()
    save_as_flow = FakeSaveAsFlow()
    flow = RsaPortalFlow(
        driver=object(),
        actions=actions,
        save_as_flow=save_as_flow,
        selectors_module=_resolved_selectors(),
    )

    destino = flow.executar_fluxo_exportacao(
        competencia="03/2026",
        cooperativa="3333",
        download_dir=tmp_path,
    )

    assert destino == tmp_path / "relatorio_3333_032026.xlsx"
    assert save_as_flow.calls == [tmp_path / "relatorio_3333_032026.xlsx"]
    assert actions.calls[0] == ("wait_element", "//div[@id='home-rsa']", "xpath", {})
    assert ("click", "//button[@id='menu-relatorios']", "xpath", {}) in actions.calls
    assert (
        "click",
        "//a[@id='menu-rsac']",
        "xpath",
        {"verify_selector": "//h6[@id='titulo-rsac']", "verify_type": "xpath"},
    ) in actions.calls
    assert ("type_into", "mes-ano", "03/2026", "id", {"verify_text": True}) in actions.calls
    assert ("click", "tipo-relatorio", "id", {}) in actions.calls
    assert ("click", "//span[.='Relatorio por Cooperativa']", "xpath", {}) in actions.calls
    assert ("click", "combo-singular", "id", {}) in actions.calls
    assert ("click", "//span[starts-with(normalize-space(), '3333 -')]", "xpath", {}) in actions.calls
    assert ("click", "//button[@value='Exportar']", "xpath", {"verify_selector": "//h6[.='Opcoes de Impressao']", "verify_type": "xpath"}) in actions.calls
    assert ("click", "formato-impressao", "id", {}) in actions.calls
    assert ("click", "//span[.='XLSX']", "xpath", {}) in actions.calls
    assert ("click", "//button[@value='Gerar Relatorio']", "xpath", {"verify_selector": "//h6[.='Relatorios Disponiveis']", "verify_type": "xpath"}) in actions.calls
    assert ("wait_element", "//table[@aria-label='Tabela de Resultados']", "xpath", {}) in actions.calls
    assert ("click", "//tr[td[1][contains(., 'Processado com sucesso')] and td[2][contains(., 'RELATORIO_RISCO_COOPERATIVA')] and td[5][contains(., 'XLSX')]]//a[@title='Imprimir Arquivo']", "xpath", {}) in actions.calls


def test_flow_uses_utils_rpa_actions_module_by_default():
    from utils import rpa_actions

    flow = RsaPortalFlow(driver=object())

    assert flow.actions is rpa_actions
