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


def _resolved_selectors():
    return SimpleNamespace(
        By=SimpleNamespace(XPATH="xpath", CSS_SELECTOR="css"),
        Screen_Sisbr=SimpleNamespace(
            BTN_MODULO_RSA="//button[@id='rsa']",
            BTN_MODULO_RSA_TIPO="xpath",
        ),
        Screen_RsaHome=SimpleNamespace(
            VALIDACAO_HOME="//div[@id='home-rsa']",
            VALIDACAO_HOME_TIPO="xpath",
        ),
        Screen_RsaFiltros=SimpleNamespace(
            INPUT_COMPETENCIA="//input[@id='competencia']",
            INPUT_COMPETENCIA_TIPO="xpath",
            INPUT_TIPO_RELATORIO="//input[@id='tipo-relatorio']",
            INPUT_TIPO_RELATORIO_TIPO="xpath",
            BTN_SELECIONAR_COOPERATIVAS="//button[@id='selecionar-coops']",
            BTN_SELECIONAR_COOPERATIVAS_TIPO="xpath",
            INPUT_BUSCA_COOPERATIVA="//input[@id='buscar-coop']",
            INPUT_BUSCA_COOPERATIVA_TIPO="xpath",
            OPCAO_COOPERATIVA_TEMPLATE="//li[@data-coop='{cooperativa}']",
            OPCAO_COOPERATIVA_TEMPLATE_TIPO="xpath",
            BTN_APLICAR_FILTROS="//button[@id='aplicar-filtros']",
            BTN_APLICAR_FILTROS_TIPO="xpath",
        ),
        Screen_RsaExportacao=SimpleNamespace(
            BTN_EXPORTAR="//button[@id='exportar']",
            BTN_EXPORTAR_TIPO="xpath",
            VALIDACAO_EXPORTACAO="//div[@id='download-concluido']",
            VALIDACAO_EXPORTACAO_TIPO="xpath",
        ),
        is_pending_selector=lambda value: False,
    )


def test_flow_raises_clear_error_when_selector_is_still_pending():
    flow = RsaPortalFlow(driver=object())

    with pytest.raises(RsaPortalPendingSelectorError, match="INPUT_COMPETENCIA"):
        flow.preencher_filtros(competencia="03/2026", tipo_relatorio="Risco Cooperativa")


def test_flow_executes_expected_sequence_when_selectors_are_ready(tmp_path: Path):
    actions = FakeActions()
    flow = RsaPortalFlow(
        driver=object(),
        actions=actions,
        selectors_module=_resolved_selectors(),
    )

    flow.abrir_modulo_rsa()
    flow.preencher_filtros(
        competencia="03/2026",
        tipo_relatorio="Risco Cooperativa",
    )
    flow.selecionar_cooperativas(["3333", "4444"])
    destino = flow.exportar_relatorio(tmp_path)

    assert destino == tmp_path
    assert actions.calls[0][0] == "click"
    assert any(call[0] == "type_into" and call[2] == "03/2026" for call in actions.calls)
    assert any(call[0] == "type_into" and call[2] == "3333" for call in actions.calls)
    assert any(call[0] == "click" and "data-coop='4444'" in call[1] for call in actions.calls)
    assert actions.calls[-1][0] == "click"


def test_flow_uses_web_rpa_actions_module_by_default():
    from rsac_relatorios_risco.web import rpa_actions

    flow = RsaPortalFlow(driver=object())

    assert flow.actions is rpa_actions
