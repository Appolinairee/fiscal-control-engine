from dataclasses import dataclass
from types import MappingProxyType
from typing import Any


@dataclass(frozen=True)
class AgentToolDefinition:
    name: str
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    safeguards: tuple[str, ...]


class AgentToolRegistry:
    def __init__(self, tools: tuple[AgentToolDefinition, ...]) -> None:
        self._tools = MappingProxyType({tool.name: tool for tool in tools})

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(self._tools.keys())

    def get(self, name: str) -> AgentToolDefinition | None:
        return self._tools.get(name)


def create_excel_tool_registry() -> AgentToolRegistry:
    return AgentToolRegistry(
        (
            AgentToolDefinition(
                name="list_sheets",
                description=(
                    "Liste les feuilles disponibles dans un fichier Excel autorise."
                ),
                input_schema={
                    "type": "object",
                    "required": ["file_path"],
                    "properties": {"file_path": {"type": "string"}},
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "sheet_names": {"type": "array", "items": {"type": "string"}},
                    },
                },
                safeguards=("allowed_file_only", "metadata_only"),
            ),
            AgentToolDefinition(
                name="get_columns",
                description="Retourne les colonnes d'une feuille Excel autorisee.",
                input_schema={
                    "type": "object",
                    "required": ["file_path", "sheet_name"],
                    "properties": {
                        "file_path": {"type": "string"},
                        "sheet_name": {"type": "string"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "sheet_name": {"type": "string"},
                        "columns": {"type": "array", "items": {"type": "string"}},
                    },
                },
                safeguards=("allowed_file_only", "metadata_only"),
            ),
            AgentToolDefinition(
                name="profile_sheet",
                description=(
                    "Produit un profil statistique d'une feuille Excel sans exposer "
                    "les valeurs des cellules."
                ),
                input_schema={
                    "type": "object",
                    "required": ["file_path", "sheet_name"],
                    "properties": {
                        "file_path": {"type": "string"},
                        "sheet_name": {"type": "string"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "sheet_name": {"type": "string"},
                        "row_count": {"type": "integer"},
                        "column_count": {"type": "integer"},
                        "columns": {"type": "array"},
                    },
                },
                safeguards=(
                    "allowed_file_only",
                    "metadata_only",
                    "never_return_cell_values",
                ),
            ),
        ),
    )
