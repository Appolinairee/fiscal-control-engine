from pathlib import Path

import pytest

from app.excel_agent.excel_tools import ExcelAgentTools
from app.excel_agent.tests.fixtures import write_minified_grand_livre
from app.excel_agent.tool_executor import ExcelToolExecutor
from app.excel_agent.tool_registry import create_excel_tool_registry
from app.excel_agent.tool_validator import (
    InvalidToolArgumentsError,
    UnknownToolError,
)
from app.llm.domain import ToolCall


def test_validator_accepts_known_tool_with_valid_arguments(tmp_path: Path) -> None:
    workbook_path = write_minified_grand_livre(tmp_path)
    executor = _create_executor(tmp_path)

    result = executor.validate(
        ToolCall(
            name="profile_sheet",
            arguments={
                "file_path": str(workbook_path),
                "sheet_name": "Grand Livre",
            },
        ),
    )

    assert result.name == "profile_sheet"
    assert result.arguments["sheet_name"] == "Grand Livre"


def test_validator_rejects_unknown_tool(tmp_path: Path) -> None:
    executor = _create_executor(tmp_path)

    with pytest.raises(UnknownToolError, match="unknown tool"):
        executor.validate(ToolCall(name="delete_file", arguments={}))


def test_validator_rejects_missing_required_argument(tmp_path: Path) -> None:
    executor = _create_executor(tmp_path)

    with pytest.raises(InvalidToolArgumentsError, match="sheet_name"):
        executor.validate(
            ToolCall(
                name="profile_sheet",
                arguments={"file_path": "grand_livre_minifie.xlsx"},
            ),
        )


def test_validator_rejects_invalid_argument_type(tmp_path: Path) -> None:
    executor = _create_executor(tmp_path)

    with pytest.raises(InvalidToolArgumentsError, match="file_path"):
        executor.validate(
            ToolCall(
                name="list_sheets",
                arguments={"file_path": 123},
            ),
        )


def test_executor_rejects_file_outside_allowed_root(tmp_path: Path) -> None:
    allowed_root = tmp_path / "allowed"
    forbidden_root = tmp_path / "forbidden"
    allowed_root.mkdir()
    forbidden_root.mkdir()
    workbook_path = write_minified_grand_livre(forbidden_root)
    executor = _create_executor(allowed_root)

    result = executor.execute(
        ToolCall(name="list_sheets", arguments={"file_path": str(workbook_path)}),
    )

    assert result.ok is False
    assert result.error_code == "unsafe_excel_path"
    assert result.output == {}


def test_executor_rejects_missing_file(tmp_path: Path) -> None:
    executor = _create_executor(tmp_path)

    result = executor.execute(
        ToolCall(
            name="list_sheets",
            arguments={"file_path": str(tmp_path / "missing.xlsx")},
        ),
    )

    assert result.ok is False
    assert result.error_code == "excel_file_read"


def test_executor_rejects_invalid_excel_file(tmp_path: Path) -> None:
    invalid_workbook = tmp_path / "invalid.xlsx"
    invalid_workbook.write_text("not a real workbook", encoding="utf-8")
    executor = _create_executor(tmp_path)

    result = executor.execute(
        ToolCall(
            name="list_sheets",
            arguments={"file_path": str(invalid_workbook)},
        ),
    )

    assert result.ok is False
    assert result.error_code == "excel_file_read"


def test_executor_profiles_minified_grand_livre_without_cell_values(
    tmp_path: Path,
) -> None:
    workbook_path = write_minified_grand_livre(tmp_path)
    executor = _create_executor(tmp_path)

    result = executor.execute(
        ToolCall(
            name="profile_sheet",
            arguments={
                "file_path": str(workbook_path),
                "sheet_name": "Grand Livre",
            },
        ),
    )

    assert result.ok is True
    assert result.error_code is None
    assert result.output["sheet_name"] == "Grand Livre"
    assert result.output["row_count"] == 4
    assert result.output["column_count"] == 5
    assert result.output["columns"][0]["name"] == "Compte"
    serialized_output = repr(result.output)
    assert "Achat fournitures" not in serialized_output
    assert "Compte a analyser" not in serialized_output


def test_executor_analyzes_minified_grand_livre_without_cell_values(
    tmp_path: Path,
) -> None:
    workbook_path = write_minified_grand_livre(tmp_path)
    executor = _create_executor(tmp_path)

    result = executor.execute(
        ToolCall(
            name="analyze_ledger",
            arguments={
                "file_path": str(workbook_path),
                "sheet_name": "Grand Livre",
            },
        ),
    )

    assert result.ok is True
    assert result.output["sheet_name"] == "Grand Livre"
    assert result.output["row_count"] == 4
    assert result.output["schema"]["is_valid"] is True
    assert result.output["schema"]["missing_required_columns"] == []
    assert result.output["columns"][0]["name"] == "Compte"
    serialized_output = repr(result.output)
    assert "Achat fournitures" not in serialized_output
    assert "Compte a analyser" not in serialized_output
    assert "601000" not in serialized_output


def _create_executor(allowed_root: Path) -> ExcelToolExecutor:
    return ExcelToolExecutor(
        tools=ExcelAgentTools(allowed_root=allowed_root),
        registry=create_excel_tool_registry(),
    )
