from rsac_relatorios_risco.config.placeholder_resolver import resolve_value


def test_resolve_supported_placeholders_in_literal_and_formula_string():
    ctx = {"Data": "032026", "YYYY-MM": "2026-03"}

    assert resolve_value("{Data}", ctx) == "032026"
    assert resolve_value("saida/{YYYY-MM}", ctx) == "saida/2026-03"
    assert (
        resolve_value('=D2 & "_RSAC_RISCO_{Data}"', ctx)
        == '=D2 & "_RSAC_RISCO_032026"'
    )
