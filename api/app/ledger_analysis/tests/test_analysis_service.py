from pathlib import Path

import pandas as pd

from app.excel_agent.excel_tools import ExcelAgentTools
from app.excel_agent.tests.fixtures import write_minified_grand_livre
from app.ledger_analysis.analysis_service import LedgerAnalysisService


def test_service_builds_minified_grand_livre_report(tmp_path: Path) -> None:
    workbook_path = write_minified_grand_livre(tmp_path)
    service = LedgerAnalysisService(excel_tools=ExcelAgentTools(allowed_root=tmp_path))

    report = service.analyze(workbook_path, sheet_name="Grand Livre")

    assert report.sheet_name == "Grand Livre"
    assert report.row_count == 4
    assert report.column_count == 5
    assert report.schema_report.is_valid is True
    assert report.schema_report.missing_required_columns == ()
    assert [column.name for column in report.columns] == [
        "Compte",
        "Date comptable",
        "Libelle",
        "Debit",
        "Credit",
    ]


def test_service_report_does_not_expose_cell_values(tmp_path: Path) -> None:
    workbook_path = write_minified_grand_livre(tmp_path)
    service = LedgerAnalysisService(excel_tools=ExcelAgentTools(allowed_root=tmp_path))

    report = service.analyze(workbook_path, sheet_name="Grand Livre")

    serialized_report = repr(report)
    assert "Achat fournitures" not in serialized_report
    assert "Compte a analyser" not in serialized_report
    assert "601000" not in serialized_report


def test_service_reports_grand_livre_with_missing_required_column(
    tmp_path: Path,
) -> None:
    workbook_path = tmp_path / "invalid_grand_livre.xlsx"
    dataframe = pd.DataFrame(
        {
            "Date comptable": ["2026-01-01"],
            "Libelle": ["Achat fournitures"],
            "Debit": [1200.0],
            "Credit": [None],
        },
    )
    with pd.ExcelWriter(workbook_path, engine="openpyxl") as writer:
        dataframe.to_excel(writer, sheet_name="Grand Livre", index=False)
    service = LedgerAnalysisService(excel_tools=ExcelAgentTools(allowed_root=tmp_path))

    report = service.analyze(workbook_path, sheet_name="Grand Livre")

    assert report.schema_report.is_valid is False
    assert report.schema_report.missing_required_columns == ("account",)
