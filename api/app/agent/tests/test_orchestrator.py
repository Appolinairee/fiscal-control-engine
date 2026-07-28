from pathlib import Path

from app.agent.orchestrator import AgentOrchestrator, AgentRunRequest
from app.excel_agent.excel_tools import ExcelAgentTools
from app.excel_agent.tests.fixtures import write_minified_grand_livre
from app.excel_agent.tool_executor import ExcelToolExecutor
from app.excel_agent.tool_registry import create_excel_tool_registry
from app.llm.domain import (
    ModelProvider,
    ModelProviderError,
    ModelRequest,
    ModelResponse,
    ToolCall,
)
from app.llm.fallback_model import FallbackModelProvider


def test_orchestrator_returns_model_answer_without_tool_call(tmp_path: Path) -> None:
    orchestrator = _create_orchestrator(
        tmp_path,
        FakeModelProvider(
            responses=(
                ModelResponse(
                    text="Je peux analyser le Grand Livre fourni.",
                    provider_name="fake",
                    model_name="fake-model",
                    finish_reason="stop",
                    tool_calls=(),
                ),
            ),
        ),
    )

    result = orchestrator.run(
        AgentRunRequest(
            user_message="Que peux-tu faire ?",
            file_path=None,
            allowed_tools=("profile_sheet",),
        ),
    )

    assert result.answer == "Je peux analyser le Grand Livre fourni."
    assert result.tool_results == ()


def test_orchestrator_executes_excel_tool_then_requests_final_answer(
    tmp_path: Path,
) -> None:
    workbook_path = write_minified_grand_livre(tmp_path)
    model = FakeModelProvider(
        responses=(
            ModelResponse(
                text="",
                provider_name="fake",
                model_name="fake-model",
                finish_reason="tool_calls",
                tool_calls=(
                    ToolCall(
                        name="profile_sheet",
                        arguments={
                            "file_path": str(workbook_path),
                            "sheet_name": "Grand Livre",
                        },
                    ),
                ),
            ),
            ModelResponse(
                text="Le fichier contient 4 lignes et 5 colonnes.",
                provider_name="fake",
                model_name="fake-model",
                finish_reason="stop",
                tool_calls=(),
            ),
        ),
    )
    orchestrator = _create_orchestrator(tmp_path, model)

    result = orchestrator.run(
        AgentRunRequest(
            user_message="Profile ce Grand Livre.",
            file_path=workbook_path,
            allowed_tools=("profile_sheet",),
        ),
    )

    assert result.answer == "Le fichier contient 4 lignes et 5 colonnes."
    assert result.tool_results[0].ok is True
    assert result.tool_results[0].output["row_count"] == 4
    assert model.calls == 2
    assert "row_count" in model.requests[1].messages[-1].content


def test_orchestrator_refuses_disallowed_tool_call(tmp_path: Path) -> None:
    workbook_path = write_minified_grand_livre(tmp_path)
    model = FakeModelProvider(
        responses=(
            ModelResponse(
                text="",
                provider_name="fake",
                model_name="fake-model",
                finish_reason="tool_calls",
                tool_calls=(
                    ToolCall(
                        name="delete_file",
                        arguments={"file_path": str(workbook_path)},
                    ),
                ),
            ),
        ),
    )
    orchestrator = _create_orchestrator(tmp_path, model)

    result = orchestrator.run(
        AgentRunRequest(
            user_message="Supprime le fichier.",
            file_path=workbook_path,
            allowed_tools=("profile_sheet",),
        ),
    )

    assert result.answer == "Le tool call a ete refuse par les garde-fous."
    assert result.tool_results[0].ok is False
    assert result.tool_results[0].error_code == "tool_not_allowed"
    assert model.calls == 1


def test_orchestrator_limits_tool_calls(tmp_path: Path) -> None:
    workbook_path = write_minified_grand_livre(tmp_path)
    model = FakeModelProvider(
        responses=(
            ModelResponse(
                text="",
                provider_name="fake",
                model_name="fake-model",
                finish_reason="tool_calls",
                tool_calls=(
                    ToolCall(
                        name="list_sheets",
                        arguments={"file_path": str(workbook_path)},
                    ),
                    ToolCall(
                        name="profile_sheet",
                        arguments={
                            "file_path": str(workbook_path),
                            "sheet_name": "Grand Livre",
                        },
                    ),
                ),
            ),
            ModelResponse(
                text="Premier tool execute seulement.",
                provider_name="fake",
                model_name="fake-model",
                finish_reason="stop",
                tool_calls=(),
            ),
        ),
    )
    orchestrator = AgentOrchestrator(
        model_provider=model,
        tool_executor=ExcelToolExecutor(
            tools=ExcelAgentTools(allowed_root=tmp_path),
            registry=create_excel_tool_registry(),
        ),
        max_tool_calls=1,
    )

    result = orchestrator.run(
        AgentRunRequest(
            user_message="Analyse le fichier.",
            file_path=workbook_path,
            allowed_tools=("list_sheets", "profile_sheet"),
        ),
    )

    assert len(result.tool_results) == 1
    assert result.tool_results[0].tool_name == "list_sheets"


def test_orchestrator_uses_model_fallback(tmp_path: Path) -> None:
    fallback_model = FallbackModelProvider(
        (
            FakeModelProvider(error=ModelProviderError()),
            FakeModelProvider(
                responses=(
                    ModelResponse(
                        text="Reponse du modele fallback.",
                        provider_name="secondary",
                        model_name="model-b",
                        finish_reason="stop",
                        tool_calls=(),
                    ),
                ),
            ),
        ),
    )
    orchestrator = _create_orchestrator(tmp_path, fallback_model)

    result = orchestrator.run(
        AgentRunRequest(
            user_message="Analyse le fichier.",
            file_path=None,
            allowed_tools=("profile_sheet",),
        ),
    )

    assert result.answer == "Reponse du modele fallback."


def test_orchestrator_blocks_direct_tax_decision_in_answer(tmp_path: Path) -> None:
    orchestrator = _create_orchestrator(
        tmp_path,
        FakeModelProvider(
            responses=(
                ModelResponse(
                    text="Decision: soumisRas=true avec taux RAS 12.5%.",
                    provider_name="fake",
                    model_name="fake-model",
                    finish_reason="stop",
                    tool_calls=(),
                ),
            ),
        ),
    )

    result = orchestrator.run(
        AgentRunRequest(
            user_message="Ce compte est-il soumis a la RAS ?",
            file_path=None,
            allowed_tools=("profile_sheet",),
        ),
    )

    assert result.answer == (
        "La reponse du modele a ete bloquee: seule une explication appuyee "
        "sur les controles deterministes est autorisee."
    )


def test_orchestrator_blocks_oversized_answer(tmp_path: Path) -> None:
    orchestrator = AgentOrchestrator(
        model_provider=FakeModelProvider(
            responses=(
                ModelResponse(
                    text="x" * 51,
                    provider_name="fake",
                    model_name="fake-model",
                    finish_reason="stop",
                    tool_calls=(),
                ),
            ),
        ),
        tool_executor=ExcelToolExecutor(
            tools=ExcelAgentTools(allowed_root=tmp_path),
            registry=create_excel_tool_registry(),
        ),
        max_answer_characters=50,
    )

    result = orchestrator.run(
        AgentRunRequest(
            user_message="Resume.",
            file_path=None,
            allowed_tools=("profile_sheet",),
        ),
    )

    assert result.answer == "La reponse du modele est trop longue pour etre retournee."


def _create_orchestrator(
    allowed_root: Path,
    model_provider: ModelProvider,
) -> AgentOrchestrator:
    return AgentOrchestrator(
        model_provider=model_provider,
        tool_executor=ExcelToolExecutor(
            tools=ExcelAgentTools(allowed_root=allowed_root),
            registry=create_excel_tool_registry(),
        ),
    )


class FakeModelProvider:
    provider_name = "fake"

    def __init__(
        self,
        responses: tuple[ModelResponse, ...] = (),
        error: Exception | None = None,
    ) -> None:
        self._responses = list(responses)
        self._error = error
        self.calls = 0
        self.requests: list[ModelRequest] = []

    def generate(self, request: ModelRequest) -> ModelResponse:
        self.calls += 1
        self.requests.append(request)
        if self._error is not None:
            raise self._error
        if not self._responses:
            raise AssertionError("fake response is required")
        return self._responses.pop(0)
