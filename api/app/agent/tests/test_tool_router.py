from pathlib import Path

from app.agent.tool_router import (
    DeterministicToolRouteRequest,
    route_deterministic_tool_calls,
)


def test_tool_router_selects_data_quality_tool_for_quality_intent() -> None:
    tool_calls = route_deterministic_tool_calls(
        DeterministicToolRouteRequest(
            user_message="Vérifie les anomalies et la qualité du fichier.",
            file_path=Path("ledger.xlsx"),
            sheet_name="Grand Livre",
            allowed_tools=("detect_data_quality_issues", "detect_tax_candidates"),
        ),
    )

    assert [tool_call.name for tool_call in tool_calls] == [
        "detect_data_quality_issues",
    ]


def test_tool_router_selects_tax_candidates_tool_for_tax_intent() -> None:
    tool_calls = route_deterministic_tool_calls(
        DeterministicToolRouteRequest(
            user_message="Trouve les candidats RAS à revoir.",
            file_path=Path("ledger.xlsx"),
            sheet_name="Grand Livre",
            allowed_tools=("detect_data_quality_issues", "detect_tax_candidates"),
        ),
    )

    assert [tool_call.name for tool_call in tool_calls] == [
        "detect_tax_candidates",
    ]


def test_tool_router_requires_file_and_sheet() -> None:
    tool_calls = route_deterministic_tool_calls(
        DeterministicToolRouteRequest(
            user_message="Vérifie la qualité.",
            file_path=Path("ledger.xlsx"),
            sheet_name=None,
            allowed_tools=("detect_data_quality_issues",),
        ),
    )

    assert tool_calls == ()
