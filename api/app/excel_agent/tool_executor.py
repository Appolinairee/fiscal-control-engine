from pathlib import Path

from app.excel_agent.domain import (
    ExcelAgentError,
    ExcelColumnList,
    ExcelColumnProfile,
    ExcelSheetList,
    ExcelSheetProfile,
    ToolExecutionResult,
    ValidatedToolCall,
)
from app.excel_agent.excel_tools import ExcelAgentTools
from app.excel_agent.tool_registry import AgentToolRegistry
from app.excel_agent.tool_validator import ToolCallValidationError, ToolCallValidator
from app.ledger_analysis.analysis_service import (
    LedgerAnalysisReport,
    LedgerAnalysisService,
)
from app.ledger_analysis.schema_validator import LedgerSchemaValidationError
from app.llm.domain import ToolCall

ToolResult = ExcelSheetList | ExcelColumnList | ExcelSheetProfile | LedgerAnalysisReport


class ExcelToolExecutor:
    def __init__(self, tools: ExcelAgentTools, registry: AgentToolRegistry) -> None:
        self._tools = tools
        self._ledger_analysis_service = LedgerAnalysisService(excel_tools=tools)
        self._validator = ToolCallValidator(registry=registry)

    def validate(self, tool_call: ToolCall) -> ValidatedToolCall:
        return self._validator.validate(tool_call)

    def execute(self, tool_call: ToolCall) -> ToolExecutionResult:
        try:
            validated_call = self._validator.validate(tool_call)
            result: ToolResult
            if validated_call.name == "list_sheets":
                result = self._tools.list_sheets(
                    Path(str(validated_call.arguments["file_path"])),
                )
            elif validated_call.name == "get_columns":
                result = self._tools.get_columns(
                    Path(str(validated_call.arguments["file_path"])),
                    sheet_name=str(validated_call.arguments["sheet_name"]),
                )
            elif validated_call.name == "profile_sheet":
                result = self._tools.profile_sheet(
                    Path(str(validated_call.arguments["file_path"])),
                    sheet_name=str(validated_call.arguments["sheet_name"]),
                )
            elif validated_call.name == "analyze_ledger":
                result = self._ledger_analysis_service.analyze(
                    Path(str(validated_call.arguments["file_path"])),
                    sheet_name=str(validated_call.arguments["sheet_name"]),
                )
            else:
                return _failed(tool_call.name, "unknown_tool", "unknown tool")
        except ToolCallValidationError as exc:
            return _failed(tool_call.name, "invalid_tool_call", str(exc))
        except LedgerSchemaValidationError as exc:
            return _failed(tool_call.name, "ledger_schema_invalid", str(exc))
        except ExcelAgentError as exc:
            return _failed(tool_call.name, _error_code(exc), str(exc))

        return ToolExecutionResult(
            tool_name=tool_call.name,
            ok=True,
            output=_serialize_result(result),
        )


def _serialize_result(
    result: ToolResult,
) -> dict[str, object]:
    if isinstance(result, ExcelSheetList):
        return {"sheet_names": list(result.sheet_names)}
    if isinstance(result, ExcelColumnList):
        return {
            "sheet_name": result.sheet_name,
            "columns": list(result.columns),
        }
    if isinstance(result, ExcelSheetProfile):
        return {
            "sheet_name": result.sheet_name,
            "row_count": result.row_count,
            "column_count": result.column_count,
            "columns": [_serialize_column(column) for column in result.columns],
        }
    return {
        "sheet_name": result.sheet_name,
        "row_count": result.row_count,
        "column_count": result.column_count,
        "schema": {
            "is_valid": result.schema_report.is_valid,
            "present_columns": list(result.schema_report.present_columns),
            "missing_required_columns": list(
                result.schema_report.missing_required_columns,
            ),
            "optional_columns": list(result.schema_report.optional_columns),
        },
        "columns": [_serialize_column(column) for column in result.columns],
    }


def _serialize_column(column: ExcelColumnProfile) -> dict[str, object]:
    return {
        "name": column.name,
        "position": column.position,
        "detected_type": column.detected_type,
        "non_empty_count": column.non_empty_count,
        "missing_count": column.missing_count,
        "missing_ratio": column.missing_ratio,
    }


def _failed(tool_name: str, error_code: str, message: str) -> ToolExecutionResult:
    return ToolExecutionResult(
        tool_name=tool_name,
        ok=False,
        output={},
        error_code=error_code,
        error_message=message,
    )


def _error_code(error: ExcelAgentError) -> str:
    error_name = type(error).__name__
    return "".join(
        f"_{character.lower()}" if character.isupper() else character
        for character in error_name.removesuffix("Error")
    ).lstrip("_")
