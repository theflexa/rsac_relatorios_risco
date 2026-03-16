from pathlib import Path

from rsac_relatorios_risco.services.report_service import read_report


REPORT_PATH = Path(
    "Models/rpas1004_00_RELATORIO_RISCO_COOPERATIVA_20260313_182416_0644.XLSX.XLSX.XLSX",
)


def test_read_report_extracts_metadata_and_rows():
    report = read_report(REPORT_PATH)

    assert report.cooperativa == "3042"
    assert report.competencia == "03/2026"
    assert report.headers == [
        "Central",
        "Singular",
        "CPF/CNPJ",
        "Nome/Razão Social",
        "Data-base",
        "Classificação de RSAC vigente",
        "Classificação por avaliação",
        "Tipo da avaliação",
        "Data da avaliação",
        "QRSAC Mobile",
        "Usuário",
    ]
    assert len(report.rows) > 0
    assert report.rows[0][1] == "3042 - SICOOB AGRORURAL"
    assert report.rows[0][4] == "03/2026"
