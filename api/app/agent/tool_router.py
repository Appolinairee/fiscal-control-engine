import re
from dataclasses import dataclass
from pathlib import Path
from unicodedata import normalize

from app.llm.domain import ToolCall


@dataclass(frozen=True)
class DeterministicToolRouteRequest:
    user_message: str
    file_path: Path | None
    sheet_name: str | None
    allowed_tools: tuple[str, ...]


def route_deterministic_tool_calls(
    request: DeterministicToolRouteRequest,
) -> tuple[ToolCall, ...]:
    if request.file_path is None or request.sheet_name is None:
        return ()

    message = _normalize_for_intent(request.user_message)
    requested_tools: list[str] = []
    query_filters = _ledger_query_filters(message)
    if query_filters and "query_ledger_entries" in request.allowed_tools:
        return (
            ToolCall(
                name="query_ledger_entries",
                arguments={
                    "file_path": str(request.file_path),
                    "sheet_name": request.sheet_name,
                    "filters": query_filters,
                    "page": 1,
                    "page_size": 20,
                },
            ),
        )
    if _mentions_data_quality(message):
        requested_tools.append("detect_data_quality_issues")
    if _mentions_tax_candidates(message):
        requested_tools.append("detect_tax_candidates")

    return tuple(
        ToolCall(
            name=tool_name,
            arguments={
                "file_path": str(request.file_path),
                "sheet_name": request.sheet_name,
            },
        )
        for tool_name in requested_tools
        if tool_name in request.allowed_tools
    )


def _mentions_data_quality(message: str) -> bool:
    return any(
        keyword in message
        for keyword in (
            "qualite",
            "anomalie",
            "colonnes vides",
            "valeurs manquantes",
            "donnees incoherentes",
            "periode suspecte",
            "tiers absent",
        )
    )


def _ledger_query_filters(message: str) -> dict[str, object]:
    account = _extract_account_filter(message)
    if account is None:
        return {}
    return {"account": account}


def _extract_account_filter(message: str) -> str | None:
    account_match = re.search(r"\b(?:compte|account)\s+([0-9]{5,12})\b", message)
    if account_match is not None:
        return account_match.group(1)
    return None


def _mentions_tax_candidates(message: str) -> bool:
    return any(
        keyword in message
        for keyword in (
            "candidat fiscal",
            "candidats fiscaux",
            "candidat ras",
            "candidats ras",
            "retenue",
            "ras",
            "tva",
            "fiscal",
        )
    )


def _normalize_for_intent(value: str) -> str:
    without_accents = normalize("NFKD", value)
    ascii_value = without_accents.encode("ascii", "ignore").decode("ascii")
    return " ".join(ascii_value.lower().split())
