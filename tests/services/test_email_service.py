from rsac_relatorios_risco.services.email_service import (
    build_summary_body,
    build_summary_subject,
    build_summary_html,
)


def test_build_summary_subject_and_body_include_concluded_pending_and_errors():
    subject = build_summary_subject(status="parcial", competencia="03/2026")
    body = build_summary_body(
        competencia="03/2026",
        concluidos=["3333", "4444"],
        pendentes=["5555"],
        erros=["Falha ao subir SharePoint da 4444"],
    )

    assert subject == "RSAC 03/2026 - parcial"
    assert "Competência: 03/2026" in body
    assert "Concluídos: 3333, 4444" in body
    assert "Pendentes: 5555" in body
    assert "Erros: Falha ao subir SharePoint da 4444" in body


def test_build_summary_html_includes_table_with_results():
    html = build_summary_html(
        concluidos=["3042", "4001"],
        erros=["5555"],
        competencia="04/2026",
    )

    assert "3042" in html
    assert "4001" in html
    assert "5555" in html
    assert "Sucesso" in html
    assert "Erro" in html
    assert "04/2026" in html
    assert "SICOOB NOVA CENTRAL" in html
    assert "Resultado do Processamento" in html
