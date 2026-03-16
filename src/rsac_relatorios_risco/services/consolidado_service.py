from pathlib import Path

from openpyxl import load_workbook

from rsac_relatorios_risco.services.report_service import ReportData


class TableMatchError(RuntimeError):
    pass


class ConsolidadoService:
    def find_header_row(self, sheet, expected_headers: list[str]) -> int:
        matches: list[int] = []
        for row_index in range(1, sheet.max_row + 1):
            row_values = [
                sheet.cell(row=row_index, column=column_index).value
                for column_index in range(1, len(expected_headers) + 1)
            ]
            normalized_values = ["" if value is None else str(value) for value in row_values]
            if normalized_values == expected_headers:
                matches.append(row_index)
        return self._validate_header_matches(matches)

    def _validate_header_matches(self, matches: list[int]) -> int:
        if not matches:
            raise TableMatchError("Nenhum cabeçalho correspondente foi encontrado")
        if len(matches) > 1:
            raise TableMatchError("Mais de um cabeçalho correspondente foi encontrado")
        return matches[0]

    def apply_report(self, workbook_path: Path, report: ReportData) -> None:
        workbook = load_workbook(workbook_path)
        sheet = workbook[report.cooperativa]
        header_row = self.find_header_row(sheet, report.headers)
        table_width = len(report.headers)
        first_data_row = header_row + 1
        last_data_row = self._find_last_data_row(sheet, first_data_row, table_width)

        for row_index in range(first_data_row, last_data_row + 1):
            for column_index in range(1, table_width + 1):
                sheet.cell(row=row_index, column=column_index).value = None

        for row_offset, row_values in enumerate(report.rows, start=first_data_row):
            for column_index, value in enumerate(row_values, start=1):
                sheet.cell(row=row_offset, column=column_index).value = value

        workbook.save(workbook_path)

    def _find_last_data_row(self, sheet, first_data_row: int, table_width: int) -> int:
        last_data_row = first_data_row - 1
        for row_index in range(first_data_row, sheet.max_row + 1):
            row_has_data = any(
                sheet.cell(row=row_index, column=column_index).value is not None
                for column_index in range(1, table_width + 1)
            )
            if row_has_data:
                last_data_row = row_index
        return last_data_row
