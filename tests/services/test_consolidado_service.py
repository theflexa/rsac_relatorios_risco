from pathlib import Path

import pytest
from openpyxl import Workbook, load_workbook

from rsac_relatorios_risco.services.consolidado_service import (
    ConsolidadoService,
    TableMatchError,
)
from rsac_relatorios_risco.services.report_service import ReportData


HEADERS = [
    "Central",
    "Singular",
    "CPF/CNPJ",
    "Nome/Razão Social",
    "Data-base",
    "Classificação de RSAC vigente",
]


def _build_workbook_with_sheet(
    tmp_path: Path,
    *,
    sheet_name: str = "3333",
    header_rows: list[int] | None = None,
) -> Path:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = sheet_name
    sheet["A1"] = "Título"
    sheet["B2"] = "Critérios"
    rows_to_create = [6] if header_rows is None else header_rows
    for header_row in rows_to_create:
        for column_index, header in enumerate(HEADERS, start=1):
            sheet.cell(row=header_row, column=column_index, value=header)
    sheet["L7"] = "preservar"
    sheet["L8"] = "preservar"
    path = tmp_path / "consolidado.xlsx"
    workbook.save(path)
    return path


def _sample_report() -> ReportData:
    return ReportData(
        cooperativa="3333",
        competencia="03/2026",
        headers=HEADERS,
        rows=[
            [
                "1004 - SICOOB NOVA CENTRAL",
                "3333 - SICOOB SECOVICRED",
                "111.111.111-11",
                "Novo Nome 1",
                "03/2026",
                "Baixo",
            ],
            [
                "1004 - SICOOB NOVA CENTRAL",
                "3333 - SICOOB SECOVICRED",
                "222.222.222-22",
                "Novo Nome 2",
                "03/2026",
                "Alto",
            ],
        ],
    )


def test_find_header_row_returns_single_exact_match(tmp_path: Path):
    workbook_path = _build_workbook_with_sheet(tmp_path)

    workbook = load_workbook(workbook_path)
    sheet = workbook["3333"]
    service = ConsolidadoService()

    assert service.find_header_row(sheet, HEADERS) == 6


def test_find_header_row_raises_when_no_match_exists(tmp_path: Path):
    workbook_path = _build_workbook_with_sheet(tmp_path, header_rows=[])

    workbook = load_workbook(workbook_path)
    sheet = workbook["3333"]
    service = ConsolidadoService()

    with pytest.raises(TableMatchError, match="Nenhum cabeçalho"):
        service.find_header_row(sheet, HEADERS)


def test_find_header_row_raises_when_more_than_one_match_exists(tmp_path: Path):
    workbook_path = _build_workbook_with_sheet(tmp_path, header_rows=[6, 12])

    workbook = load_workbook(workbook_path)
    sheet = workbook["3333"]
    service = ConsolidadoService()

    with pytest.raises(TableMatchError, match="Mais de um cabeçalho"):
        service.find_header_row(sheet, HEADERS)


def test_apply_report_clears_only_table_data_and_rewrites_rows(tmp_path: Path):
    workbook_path = _build_workbook_with_sheet(tmp_path)
    workbook = load_workbook(workbook_path)
    sheet = workbook["3333"]
    old_rows = [
        [
            "1004 - SICOOB NOVA CENTRAL",
            "3333 - SICOOB SECOVICRED",
            "999.999.999-99",
            "Nome Antigo 1",
            "01/2026",
            "Médio",
        ],
        [
            "1004 - SICOOB NOVA CENTRAL",
            "3333 - SICOOB SECOVICRED",
            "888.888.888-88",
            "Nome Antigo 2",
            "01/2026",
            "Baixo",
        ],
    ]
    for row_index, row_values in enumerate(old_rows, start=7):
        for column_index, value in enumerate(row_values, start=1):
            sheet.cell(row=row_index, column=column_index, value=value)
    workbook.save(workbook_path)

    service = ConsolidadoService()
    service.apply_report(workbook_path, _sample_report())

    updated_workbook = load_workbook(workbook_path)
    updated_sheet = updated_workbook["3333"]

    assert updated_sheet["A6"].value == "Central"
    assert updated_sheet["C7"].value == "111.111.111-11"
    assert updated_sheet["D8"].value == "Novo Nome 2"
    assert updated_sheet["E9"].value is None
    assert updated_sheet["L7"].value == "preservar"
    assert updated_sheet["L8"].value == "preservar"
