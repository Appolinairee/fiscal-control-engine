from dataclasses import dataclass
from pathlib import Path

from app.excel_agent.domain import ExcelColumnProfile
from app.excel_agent.excel_tools import ExcelAgentTools
from app.ledger_analysis.schema_validator import (
    LedgerSchemaReport,
    LedgerSchemaValidator,
)


@dataclass(frozen=True)
class LedgerAnalysisReport:
    sheet_name: str
    row_count: int
    column_count: int
    schema_report: LedgerSchemaReport
    columns: tuple[ExcelColumnProfile, ...]


class LedgerAnalysisService:
    def __init__(
        self,
        excel_tools: ExcelAgentTools,
        schema_validator: LedgerSchemaValidator | None = None,
    ) -> None:
        self._excel_tools = excel_tools
        self._schema_validator = schema_validator or LedgerSchemaValidator()

    def analyze(self, file_path: Path, sheet_name: str) -> LedgerAnalysisReport:
        sheet_profile = self._excel_tools.profile_sheet(file_path, sheet_name)
        column_names = tuple(column.name for column in sheet_profile.columns)
        schema_report = self._schema_validator.validate(column_names)
        return LedgerAnalysisReport(
            sheet_name=sheet_profile.sheet_name,
            row_count=sheet_profile.row_count,
            column_count=sheet_profile.column_count,
            schema_report=schema_report,
            columns=sheet_profile.columns,
        )
