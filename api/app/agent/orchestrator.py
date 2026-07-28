from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from app.agent.answer_policy import AgentAnswerPolicy
from app.excel_agent.domain import ToolExecutionResult
from app.excel_agent.tool_executor import ExcelToolExecutor
from app.llm.domain import ModelMessage, ModelProvider, ModelRequest, ToolCall


@dataclass(frozen=True)
class AgentRunRequest:
    user_message: str
    file_path: Path | None
    allowed_tools: tuple[str, ...]


@dataclass(frozen=True)
class AgentRunResult:
    answer: str
    tool_results: tuple[ToolExecutionResult, ...]


class ToolExecutor(Protocol):
    def execute(self, tool_call: ToolCall) -> ToolExecutionResult:
        pass


class AgentOrchestrator:
    def __init__(
        self,
        model_provider: ModelProvider,
        tool_executor: ExcelToolExecutor,
        max_tool_calls: int = 3,
        max_answer_characters: int = 4_000,
    ) -> None:
        if max_tool_calls < 1:
            raise ValueError("max_tool_calls must be positive")
        self._model_provider = model_provider
        self._tool_executor = tool_executor
        self._max_tool_calls = max_tool_calls
        self._answer_policy = AgentAnswerPolicy(
            max_answer_characters=max_answer_characters,
        )

    def run(self, request: AgentRunRequest) -> AgentRunResult:
        initial_model_request = _initial_model_request(request)
        initial_response = self._model_provider.generate(initial_model_request)
        if not initial_response.tool_calls:
            return AgentRunResult(
                answer=self._answer_policy.apply(initial_response.text).answer,
                tool_results=(),
            )

        tool_results = tuple(
            self._execute_allowed_tool_call(tool_call, request.allowed_tools)
            for tool_call in initial_response.tool_calls[: self._max_tool_calls]
        )
        if any(not result.ok for result in tool_results):
            return AgentRunResult(
                answer="Le tool call a ete refuse par les garde-fous.",
                tool_results=tool_results,
            )

        final_response = self._model_provider.generate(
            _final_model_request(request, tool_results),
        )
        return AgentRunResult(
            answer=self._answer_policy.apply(final_response.text).answer,
            tool_results=tool_results,
        )

    def _execute_allowed_tool_call(
        self,
        tool_call: ToolCall,
        allowed_tools: tuple[str, ...],
    ) -> ToolExecutionResult:
        if tool_call.name not in allowed_tools:
            return ToolExecutionResult(
                tool_name=tool_call.name,
                ok=False,
                output={},
                error_code="tool_not_allowed",
                error_message=f"tool is not allowed: {tool_call.name}",
            )
        return self._tool_executor.execute(tool_call)


def _initial_model_request(request: AgentRunRequest) -> ModelRequest:
    messages = [
        ModelMessage(
            role="system",
            content=(
                "Tu es un agent d'analyse Excel. Utilise seulement les tools "
                "autorises. Ne prends aucune decision fiscale."
            ),
        ),
        ModelMessage(role="user", content=request.user_message),
    ]
    if request.file_path is not None:
        messages.append(
            ModelMessage(role="system", content=f"Fichier cible: {request.file_path}"),
        )
    return ModelRequest(
        messages=tuple(messages),
        allowed_tools=request.allowed_tools,
        temperature=0.0,
        max_output_tokens=1200,
        timeout_seconds=30.0,
    )


def _final_model_request(
    request: AgentRunRequest,
    tool_results: tuple[ToolExecutionResult, ...],
) -> ModelRequest:
    return ModelRequest(
        messages=(
            ModelMessage(
                role="system",
                content=(
                    "Redige une reponse courte a partir des resultats de tools. "
                    "Ne revele pas de donnees sensibles."
                ),
            ),
            ModelMessage(role="user", content=request.user_message),
            ModelMessage(role="tool", content=repr(tool_results)),
        ),
        allowed_tools=(),
        temperature=0.0,
        max_output_tokens=1200,
        timeout_seconds=30.0,
    )
