from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from time import monotonic
from typing import Protocol

from app.agent.answer_policy import AgentAnswerPolicy
from app.agent.constants import AGENT_RUN_TIMEOUT_ANSWER
from app.excel_agent.domain import ToolExecutionResult
from app.excel_agent.tool_executor import ExcelToolExecutor
from app.llm.domain import (
    ModelMessage,
    ModelProvider,
    ModelRequest,
    ModelToolDefinition,
    ToolCall,
)


@dataclass(frozen=True)
class AgentRunEvent:
    event_type: str
    title: str
    message: str
    status: str
    tool_name: str | None = None
    provider_name: str | None = None
    model_name: str | None = None


@dataclass(frozen=True)
class AgentRunRequest:
    user_message: str
    file_path: Path | None
    sheet_name: str | None
    allowed_tools: tuple[str, ...]
    direct_tool_call: ToolCall | None = None


@dataclass(frozen=True)
class AgentRunResult:
    answer: str
    provider_name: str
    model_name: str
    execution_events: tuple[AgentRunEvent, ...]
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
        max_run_seconds: float = 60.0,
        monotonic: Callable[[], float] = monotonic,
    ) -> None:
        if max_tool_calls < 1:
            raise ValueError("max_tool_calls must be positive")
        if max_run_seconds <= 0:
            raise ValueError("max_run_seconds must be positive")
        self._model_provider = model_provider
        self._tool_executor = tool_executor
        self._max_tool_calls = max_tool_calls
        self._max_run_seconds = max_run_seconds
        self._monotonic = monotonic
        self._answer_policy = AgentAnswerPolicy(
            max_answer_characters=max_answer_characters,
        )

    def run(
        self,
        request: AgentRunRequest,
        event_sink: Callable[[AgentRunEvent], None] | None = None,
    ) -> AgentRunResult:
        started_at = self._monotonic()
        events: list[AgentRunEvent] = []

        def emit(event: AgentRunEvent) -> None:
            events.append(event)
            if event_sink is not None:
                event_sink(event)

        emit(
            AgentRunEvent(
                event_type="run_started",
                title="Demande reçue",
                message="Demande prise en compte.",
                status="completed",
            ),
        )
        if request.file_path is not None:
            emit(
                AgentRunEvent(
                    event_type="file_checked",
                    title="Fichier disponible",
                    message="Fichier prêt pour l'analyse.",
                    status="completed",
                ),
            )
        if request.direct_tool_call is not None:
            emit(_tool_started_event(request.direct_tool_call.name))
            tool_result = self._execute_allowed_tool_call(
                request.direct_tool_call,
                request,
            )
            emit(_tool_finished_event(tool_result))
            answer = (
                "L'analyse déterministe du Grand Livre est terminée."
                if tool_result.ok
                else "L'analyse déterministe du Grand Livre a échoué."
            )
            emit(
                AgentRunEvent(
                    event_type="answer_ready",
                    title="Réponse prête",
                    message="Réponse prête.",
                    status="completed",
                    provider_name="internal",
                    model_name="direct-tool-call",
                ),
            )
            return AgentRunResult(
                answer=answer,
                provider_name="internal",
                model_name="direct-tool-call",
                execution_events=tuple(events),
                tool_results=(tool_result,),
            )
        initial_model_request = _initial_model_request(
            request,
            tool_definitions=self._tool_executor.get_model_tool_definitions(
                request.allowed_tools,
            ),
        )
        emit(
            AgentRunEvent(
                event_type="model_requested",
                title="Contexte d'analyse",
                message="Identification du contexte utile.",
                status="running",
                provider_name=self._model_provider.provider_name,
            ),
        )
        initial_response = self._model_provider.generate(initial_model_request)
        _emit_fallback_if_needed(
            provider_name=self._model_provider.provider_name,
            response_provider_name=initial_response.provider_name,
            response_model_name=initial_response.model_name,
            emit=emit,
        )
        if self._has_timed_out(started_at):
            return _timeout_result(tuple(events))
        if not initial_response.tool_calls:
            answer = self._answer_policy.apply(initial_response.text).answer
            emit(
                AgentRunEvent(
                    event_type="answer_ready",
                    title="Réponse prête",
                    message="Réponse prête.",
                    status="completed",
                    provider_name=initial_response.provider_name,
                    model_name=initial_response.model_name,
                ),
            )
            return AgentRunResult(
                answer=answer,
                provider_name=initial_response.provider_name,
                model_name=initial_response.model_name,
                execution_events=tuple(events),
                tool_results=(),
            )

        tool_results = []
        for tool_call in initial_response.tool_calls[: self._max_tool_calls]:
            emit(
                AgentRunEvent(
                    event_type="tool_requested",
                    title="Analyse préparée",
                    message=f"{_tool_user_label(tool_call.name)} prête.",
                    status="completed",
                    tool_name=tool_call.name,
                    provider_name=initial_response.provider_name,
                    model_name=initial_response.model_name,
                ),
            )
            emit(_tool_started_event(tool_call.name))
            tool_result = self._execute_allowed_tool_call(
                _with_request_context(tool_call, request),
                request,
            )
            tool_results.append(tool_result)
            emit(_tool_finished_event(tool_result))
        stable_tool_results = tuple(tool_results)
        if self._has_timed_out(started_at):
            return _timeout_result(tuple(events))
        if any(not result.ok for result in stable_tool_results):
            emit(
                AgentRunEvent(
                    event_type="run_failed",
                    title="Analyse arrêtée",
                    message="L'analyse demandée ne peut pas être exécutée.",
                    status="error",
                    provider_name=initial_response.provider_name,
                    model_name=initial_response.model_name,
                ),
            )
            return AgentRunResult(
                answer="Le tool call a ete refuse par les garde-fous.",
                provider_name=initial_response.provider_name,
                model_name=initial_response.model_name,
                execution_events=tuple(events),
                tool_results=stable_tool_results,
            )

        emit(
            AgentRunEvent(
                event_type="model_requested",
                title="Réponse en cours",
                message="Préparation de la réponse.",
                status="running",
                provider_name=self._model_provider.provider_name,
            ),
        )
        final_response = self._model_provider.generate(
            _final_model_request(request, stable_tool_results),
        )
        _emit_fallback_if_needed(
            provider_name=self._model_provider.provider_name,
            response_provider_name=final_response.provider_name,
            response_model_name=final_response.model_name,
            emit=emit,
        )
        if self._has_timed_out(started_at):
            return _timeout_result(tuple(events))
        answer = self._answer_policy.apply(final_response.text).answer
        emit(
            AgentRunEvent(
                event_type="answer_ready",
                title="Réponse prête",
                message="Réponse prête.",
                status="completed",
                provider_name=final_response.provider_name,
                model_name=final_response.model_name,
            ),
        )
        return AgentRunResult(
            answer=answer,
            provider_name=final_response.provider_name,
            model_name=final_response.model_name,
            execution_events=tuple(events),
            tool_results=stable_tool_results,
        )

    def _execute_allowed_tool_call(
        self,
        tool_call: ToolCall,
        request: AgentRunRequest,
    ) -> ToolExecutionResult:
        if tool_call.name not in request.allowed_tools:
            return ToolExecutionResult(
                tool_name=tool_call.name,
                ok=False,
                output={},
                error_code="tool_not_allowed",
                error_message=f"tool is not allowed: {tool_call.name}",
            )
        return self._tool_executor.execute(tool_call)

    def _has_timed_out(self, started_at: float) -> bool:
        return self._monotonic() - started_at > self._max_run_seconds


def _timeout_result(events: tuple[AgentRunEvent, ...] = ()) -> AgentRunResult:
    timeout_event = AgentRunEvent(
        event_type="run_failed",
        title="Temps dépassé",
        message="L'analyse a dépassé le temps autorisé.",
        status="error",
        provider_name="internal",
        model_name="timeout-guard",
    )
    return AgentRunResult(
        answer=AGENT_RUN_TIMEOUT_ANSWER,
        provider_name="internal",
        model_name="timeout-guard",
        execution_events=(*events, timeout_event),
        tool_results=(),
    )


def _emit_fallback_if_needed(
    provider_name: str,
    response_provider_name: str,
    response_model_name: str,
    emit: Callable[[AgentRunEvent], None],
) -> None:
    if provider_name != "fallback":
        return
    if response_provider_name == provider_name:
        return
    emit(
        AgentRunEvent(
            event_type="fallback_used",
            title="Moteur d'analyse disponible",
            message="Connexion au moteur d'analyse.",
            status="completed",
            provider_name=response_provider_name,
            model_name=response_model_name,
        ),
    )


def _tool_started_event(tool_name: str) -> AgentRunEvent:
    return AgentRunEvent(
        event_type="tool_started",
        title="Analyse du fichier",
        message=f"{_tool_user_label(tool_name)} en cours.",
        status="running",
        tool_name=tool_name,
    )


def _tool_finished_event(tool_result: ToolExecutionResult) -> AgentRunEvent:
    if not tool_result.ok:
        return AgentRunEvent(
            event_type="tool_finished",
            title="Analyse arrêtée",
            message="L'analyse demandée ne peut pas être exécutée.",
            status="error",
            tool_name=tool_result.tool_name,
        )
    return AgentRunEvent(
        event_type="tool_finished",
        title="Analyse terminée",
        message=_tool_result_summary(tool_result),
        status="completed",
        tool_name=tool_result.tool_name,
    )


def _tool_user_label(tool_name: str) -> str:
    labels = {
        "list_sheets": "Lecture des feuilles",
        "get_columns": "Lecture des colonnes",
        "profile_sheet": "Analyse de la feuille Excel",
        "analyze_ledger": "Analyse du Grand Livre",
    }
    return labels.get(tool_name, "Analyse demandée")


def _tool_result_summary(tool_result: ToolExecutionResult) -> str:
    if tool_result.tool_name == "profile_sheet":
        return _rows_columns_summary(
            prefix="L'analyse de la feuille Excel est terminée",
            output=tool_result.output,
        )
    if tool_result.tool_name == "analyze_ledger":
        return _rows_columns_summary(
            prefix="L'analyse du Grand Livre est terminée",
            output=tool_result.output,
        )
    if tool_result.tool_name == "list_sheets":
        sheet_count = len(tool_result.output.get("sheet_names", ()))
        return f"{sheet_count} feuille(s) détectée(s) dans le fichier."
    if tool_result.tool_name == "get_columns":
        column_count = len(tool_result.output.get("columns", ()))
        return f"{column_count} colonne(s) détectée(s) dans la feuille."
    return "L'analyse demandée est terminée."


def _rows_columns_summary(prefix: str, output: dict[str, object]) -> str:
    row_count = output.get("row_count")
    column_count = output.get("column_count")
    if isinstance(row_count, int) and isinstance(column_count, int):
        return f"{prefix}: {row_count} lignes, {column_count} colonnes."
    return f"{prefix}."


def _initial_model_request(
    request: AgentRunRequest,
    tool_definitions: tuple[ModelToolDefinition, ...],
) -> ModelRequest:
    messages = [
        ModelMessage(
            role="system",
            content=(
                "Tu es un agent d'analyse Excel. Utilise seulement les tools "
                "autorises. Ne prends aucune decision fiscale. Reponds en "
                "Markdown clair avec des paragraphes courts. Pour une reponse "
                "simple, n'ajoute pas de titre comme Introduction. Evite les "
                "formulations a la premiere personne."
            ),
        ),
        ModelMessage(role="user", content=request.user_message),
    ]
    if request.file_path is not None:
        messages.append(
            ModelMessage(role="system", content=f"Fichier cible: {request.file_path}"),
        )
    if request.sheet_name is not None:
        messages.append(
            ModelMessage(role="system", content=f"Feuille cible: {request.sheet_name}"),
        )
    return ModelRequest(
        messages=tuple(messages),
        allowed_tools=request.allowed_tools,
        temperature=0.0,
        max_output_tokens=1200,
        timeout_seconds=30.0,
        tool_definitions=tool_definitions,
    )


def _with_request_context(
    tool_call: ToolCall,
    request: AgentRunRequest,
) -> ToolCall:
    arguments = dict(tool_call.arguments)
    if request.file_path is not None:
        arguments["file_path"] = str(request.file_path)
    if request.sheet_name is not None and tool_call.name != "list_sheets":
        arguments["sheet_name"] = request.sheet_name
    return ToolCall(name=tool_call.name, arguments=arguments)


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
                    "Utilise du Markdown lisible: paragraphes courts, listes "
                    "a puces si utile, tableaux simples seulement si cela clarifie. "
                    "Pour une reponse simple, n'ajoute pas de titre comme "
                    "Introduction. Evite les formulations a la premiere personne. "
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
