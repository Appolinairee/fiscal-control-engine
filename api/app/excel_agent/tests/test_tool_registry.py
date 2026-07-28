from app.excel_agent.tool_registry import create_excel_tool_registry


def test_excel_tool_registry_exposes_initial_tools() -> None:
    registry = create_excel_tool_registry()

    assert registry.names == ("list_sheets", "get_columns", "profile_sheet")


def test_excel_tool_definitions_have_contracts_and_safeguards() -> None:
    registry = create_excel_tool_registry()

    profile_sheet = registry.get("profile_sheet")

    assert profile_sheet is not None
    assert profile_sheet.name == "profile_sheet"
    assert profile_sheet.description
    assert profile_sheet.input_schema["required"] == ["file_path", "sheet_name"]
    assert profile_sheet.output_schema["type"] == "object"
    assert "never_return_cell_values" in profile_sheet.safeguards


def test_excel_tool_registry_rejects_unknown_tool() -> None:
    registry = create_excel_tool_registry()

    assert registry.get("unknown") is None
