import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

from app.agent.orchestrator import (
    AgentOrchestrator,
    AgentRunEvent,
    AgentRunRequest,
    AgentRunResult,
)
from app.agent_file.domain import AgentFileReadError, AgentFileUploadResult
from app.config import Settings
from app.excel_agent.domain import ToolExecutionResult
from app.excel_agent.excel_tools import ExcelAgentTools
from app.excel_agent.tests.fixtures import write_minified_grand_livre
from app.excel_agent.tool_executor import ExcelToolExecutor
from app.excel_agent.tool_registry import create_excel_tool_registry
from app.llm.domain import ModelRequest, ModelResponse, ToolCall
from app.main import create_app
from app.routers.agent import (
    AgentEndpointError,
    get_agent_file_resolver,
    get_agent_file_upload_service,
    get_agent_orchestrator,
    get_api_settings,
)


def test_agent_run_endpoint_returns_orchestrated_answer() -> None:
    app = create_app()
    fake_orchestrator = FakeAgentOrchestrator(
        AgentRunResult(
            answer="Le fichier contient 4 lignes et 5 colonnes.",
            provider_name="fake",
            model_name="fake-model",
            execution_events=(
                AgentRunEvent(
                    event_type="run_started",
                    title="Demande reçue",
                    message="Demande prise en compte.",
                    status="completed",
                ),
            ),
            tool_results=(
                ToolExecutionResult(
                    tool_name="profile_sheet",
                    ok=True,
                    output={"sheet_name": "Grand Livre", "row_count": 4},
                ),
            ),
        ),
    )
    async def override_orchestrator() -> FakeAgentOrchestrator:
        return fake_orchestrator

    app.dependency_overrides[get_agent_orchestrator] = override_orchestrator

    response = _post(
        app,
        "/api/agent/runs",
        json={
            "message": "Profile ce Grand Livre.",
            "file_path": "grand_livre_minifie.xlsx",
            "allowed_tools": ["profile_sheet"],
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "answer": "Le fichier contient 4 lignes et 5 colonnes.",
        "provider_name": "fake",
        "model_name": "fake-model",
        "execution_events": [
            {
                "event_type": "run_started",
                "title": "Demande reçue",
                "message": "Demande prise en compte.",
                "status": "completed",
                "tool_name": None,
                "provider_name": None,
                "model_name": None,
            },
        ],
        "tool_results": [
            {
                "tool_name": "profile_sheet",
                "ok": True,
                "output": {"sheet_name": "Grand Livre", "row_count": 4},
                "error_code": None,
                "error_message": None,
            },
        ],
    }
    assert fake_orchestrator.last_request == AgentRunRequest(
        user_message="Profile ce Grand Livre.",
        file_path=Path("grand_livre_minifie.xlsx"),
        sheet_name=None,
        allowed_tools=("profile_sheet",),
    )


def test_agent_run_endpoint_accepts_session_file_reference() -> None:
    app = create_app()
    fake_orchestrator = FakeAgentOrchestrator(
        AgentRunResult(
            answer="OK",
            provider_name="fake",
            model_name="fake-model",
            execution_events=(),
            tool_results=(),
        ),
    )
    fake_resolver = FakeAgentFileResolver(
        resolved_path=Path("/server/session/file.xlsx"),
    )

    async def override_orchestrator() -> FakeAgentOrchestrator:
        return fake_orchestrator

    async def override_file_resolver() -> FakeAgentFileResolver:
        return fake_resolver

    app.dependency_overrides[get_agent_orchestrator] = override_orchestrator
    app.dependency_overrides[get_agent_file_resolver] = override_file_resolver

    response = _post(
        app,
        "/api/agent/runs",
        json={
            "message": "Profile le fichier de session.",
            "session_id": "session-1",
            "file_id": "file-1",
            "allowed_tools": ["profile_sheet"],
        },
    )

    assert response.status_code == 200
    assert fake_orchestrator.last_request == AgentRunRequest(
        user_message="Profile le fichier de session.",
        file_path=Path("/server/session/file.xlsx"),
        sheet_name=None,
        allowed_tools=("profile_sheet",),
    )


def test_agent_run_endpoint_allows_ledger_analysis_by_default() -> None:
    app = create_app()
    fake_orchestrator = FakeAgentOrchestrator(
        AgentRunResult(
            answer="OK",
            provider_name="fake",
            model_name="fake-model",
            execution_events=(),
            tool_results=(),
        ),
    )

    async def override_orchestrator() -> FakeAgentOrchestrator:
        return fake_orchestrator

    app.dependency_overrides[get_agent_orchestrator] = override_orchestrator

    response = _post(
        app,
        "/api/agent/runs",
        json={
            "message": "Analyse ce Grand Livre.",
            "file_path": "grand_livre_minifie.xlsx",
        },
    )

    assert response.status_code == 200
    assert fake_orchestrator.last_request is not None
    assert "analyze_ledger" in fake_orchestrator.last_request.allowed_tools


def test_agent_upload_then_run_uses_stored_session_reference(tmp_path: Path) -> None:
    app = create_app()
    source_path = write_minified_grand_livre(tmp_path / "sources")
    fake_orchestrator = FakeAgentOrchestrator(
        AgentRunResult(
            answer="OK",
            provider_name="fake",
            model_name="fake-model",
            execution_events=(),
            tool_results=(),
        ),
    )

    async def override_settings() -> Settings:
        return Settings(
            agent_file_storage_root_path=str(tmp_path / "sessions"),
            agent_file_max_upload_bytes=200_000,
        )

    async def override_orchestrator() -> FakeAgentOrchestrator:
        return fake_orchestrator

    app.dependency_overrides[get_api_settings] = override_settings
    app.dependency_overrides[get_agent_orchestrator] = override_orchestrator

    upload_response = _post_files(
        app,
        "/api/agent/files",
        files={
            "file": (
                "grand_livre.xlsx",
                source_path.read_bytes(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ),
        },
    )

    assert upload_response.status_code == 201
    upload_payload = upload_response.json()
    run_response = _post(
        app,
        "/api/agent/runs",
        json={
            "message": "Analyse ce Grand Livre.",
            "session_id": upload_payload["session_id"],
            "file_id": upload_payload["file_id"],
            "allowed_tools": ["analyze_ledger"],
        },
    )

    assert run_response.status_code == 200
    assert fake_orchestrator.last_request is not None
    assert fake_orchestrator.last_request.file_path is not None
    assert fake_orchestrator.last_request.file_path.is_file()
    assert fake_orchestrator.last_request.file_path.suffix == ".xlsx"
    assert fake_orchestrator.last_request.allowed_tools == ("analyze_ledger",)


def test_agent_upload_then_run_executes_ledger_analysis_tool(
    tmp_path: Path,
) -> None:
    app = create_app()
    source_path = write_minified_grand_livre(tmp_path / "sources")
    model = LedgerAnalysisToolCallingModel()

    async def override_settings() -> Settings:
        return Settings(
            agent_file_storage_root_path=str(tmp_path / "sessions"),
            excel_agent_allowed_root_path=str(tmp_path / "docs"),
            agent_file_max_upload_bytes=200_000,
        )

    async def override_orchestrator() -> AgentOrchestrator:
        return AgentOrchestrator(
            model_provider=model,
            tool_executor=ExcelToolExecutor(
                tools=ExcelAgentTools(
                    allowed_root=tmp_path / "docs",
                    allowed_roots=(tmp_path / "sessions",),
                ),
                registry=create_excel_tool_registry(),
            ),
        )

    app.dependency_overrides[get_api_settings] = override_settings
    app.dependency_overrides[get_agent_orchestrator] = override_orchestrator

    upload_response = _post_files(
        app,
        "/api/agent/files",
        files={
            "file": (
                "grand_livre.xlsx",
                source_path.read_bytes(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ),
        },
    )
    upload_payload = upload_response.json()

    run_response = _post(
        app,
        "/api/agent/runs",
        json={
            "message": "Analyse ce Grand Livre.",
            "session_id": upload_payload["session_id"],
            "file_id": upload_payload["file_id"],
        },
    )

    assert run_response.status_code == 200
    payload = run_response.json()
    assert payload["answer"] == "Le Grand Livre contient 4 lignes et 5 colonnes."
    assert payload["provider_name"] == "fake"
    assert payload["model_name"] == "tool-caller"
    assert [event["event_type"] for event in payload["execution_events"]] == [
        "run_started",
        "file_checked",
        "model_requested",
        "tool_requested",
        "tool_started",
        "tool_finished",
        "model_requested",
        "answer_ready",
    ]
    assert payload["tool_results"][0]["tool_name"] == "analyze_ledger"
    assert payload["tool_results"][0]["ok"] is True
    assert payload["tool_results"][0]["output"]["row_count"] == 4
    assert payload["tool_results"][0]["output"]["schema"]["is_valid"] is True


def test_agent_run_endpoint_rejects_ambiguous_file_reference() -> None:
    response = _post(
        create_app(),
        "/api/agent/runs",
        json={
            "message": "Analyse",
            "file_path": "grand_livre_minifie.xlsx",
            "session_id": "session-1",
            "file_id": "file-1",
            "allowed_tools": ["profile_sheet"],
        },
    )

    assert response.status_code == 422


def test_agent_run_endpoint_validates_message() -> None:
    response = _post(
        create_app(),
        "/api/agent/runs",
        json={"message": "", "allowed_tools": ["profile_sheet"]},
    )

    assert response.status_code == 422


def test_agent_run_endpoint_returns_sanitized_orchestrator_error() -> None:
    app = create_app()
    fake_orchestrator = FailingAgentOrchestrator(
        AgentEndpointError(
            public_code="agent_run_failed",
            public_message="L'execution agent a echoue.",
        ),
    )
    async def override_orchestrator() -> FailingAgentOrchestrator:
        return fake_orchestrator

    app.dependency_overrides[get_agent_orchestrator] = override_orchestrator

    response = _post(
        app,
        "/api/agent/runs",
        json={
            "message": "Voici un prompt confidentiel avec /secret/client.xlsx",
            "file_path": "/secret/client.xlsx",
            "allowed_tools": ["profile_sheet"],
        },
    )

    assert response.status_code == 400
    assert response.json() == {
        "error": {
            "code": "agent_run_failed",
            "message": "L'execution agent a echoue.",
        },
    }
    serialized_response = response.text
    assert "prompt confidentiel" not in serialized_response
    assert "/secret/client.xlsx" not in serialized_response


def test_agent_tools_are_not_exposed_as_individual_http_endpoints() -> None:
    response = _post(
        create_app(),
        "/api/agent/tools/profile_sheet",
        json={"file_path": "grand_livre_minifie.xlsx"},
    )

    assert response.status_code == 404


def test_agent_run_stream_endpoint_returns_events_before_final_result() -> None:
    app = create_app()
    fake_orchestrator = FakeAgentOrchestrator(
        AgentRunResult(
            answer="- Le fichier contient 4 lignes.\n- Le schema est valide.",
            provider_name="fake",
            model_name="fake-model",
            execution_events=(),
            tool_results=(),
        ),
        events=(
            AgentRunEvent(
                event_type="run_started",
                title="Demande reçue",
                message="Demande prise en compte.",
                status="completed",
            ),
            AgentRunEvent(
                event_type="tool_started",
                title="Analyse du fichier",
                message="Analyse du Grand Livre en cours.",
                status="running",
                tool_name="analyze_ledger",
            ),
        ),
    )

    async def override_orchestrator() -> FakeAgentOrchestrator:
        return fake_orchestrator

    app.dependency_overrides[get_agent_orchestrator] = override_orchestrator

    response = _post(
        app,
        "/api/agent/runs/stream",
        json={"message": "Analyse ce Grand Livre."},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/x-ndjson")
    lines = [json.loads(line) for line in response.text.splitlines()]
    assert [line["type"] for line in lines] == [
        "event",
        "event",
        "event",
        "event",
        "result",
    ]
    assert lines[0]["data"]["message"] == "Demande prise en compte."
    assert lines[1]["data"]["tool_name"] == "analyze_ledger"
    assert lines[2]["data"]["event_type"] == "answer_delta"
    assert lines[2]["data"]["message"] == "- Le fichier contient 4 lignes."
    assert lines[-1]["data"]["model_name"] == "fake-model"


def test_agent_file_upload_endpoint_returns_session_reference_only() -> None:
    app = create_app()
    fake_upload_service = FakeAgentFileUploadService(
        AgentFileUploadResult(
            session_id="session-1",
            file_id="file-1",
            original_filename="grand_livre.xlsx",
            expires_at=datetime(2026, 1, 1, 12, 0, tzinfo=UTC),
            validated_for_agent=True,
            rag_indexable=False,
            sheet_names=("Grand Livre",),
        ),
    )

    async def override_upload_service() -> FakeAgentFileUploadService:
        return fake_upload_service

    app.dependency_overrides[get_agent_file_upload_service] = override_upload_service

    response = _post_files(
        app,
        "/api/agent/files",
        files={
            "file": (
                "../client/grand_livre.xlsx",
                b"fake Excel bytes handled by service fake",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ),
        },
    )

    assert response.status_code == 201
    assert response.json() == {
        "session_id": "session-1",
        "file_id": "file-1",
        "original_filename": "grand_livre.xlsx",
        "expires_at": "2026-01-01T12:00:00Z",
        "validated_for_agent": True,
        "rag_indexable": False,
        "sheet_names": ["Grand Livre"],
    }
    assert fake_upload_service.last_original_filename == "../client/grand_livre.xlsx"
    assert fake_upload_service.last_source_path is not None
    serialized_response = response.text
    assert "fake Excel bytes" not in serialized_response
    assert "server" not in serialized_response


def test_agent_file_upload_endpoint_requires_file() -> None:
    response = _post(
        create_app(),
        "/api/agent/files",
        json={},
    )

    assert response.status_code == 422


def test_agent_file_upload_endpoint_returns_sanitized_upload_error() -> None:
    app = create_app()
    fake_upload_service = FailingAgentFileUploadService(
        AgentFileReadError("invalid Excel file at /secret/client.xlsx"),
    )

    async def override_upload_service() -> FailingAgentFileUploadService:
        return fake_upload_service

    app.dependency_overrides[get_agent_file_upload_service] = override_upload_service

    response = _post_files(
        app,
        "/api/agent/files",
        files={
            "file": (
                "client.xlsx",
                b"invalid content",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ),
        },
    )

    assert response.status_code == 400
    assert response.json() == {
        "error": {
            "code": "agent_file_invalid",
            "message": "Le fichier Excel agent est invalide ou illisible.",
        },
    }
    assert "/secret/client.xlsx" not in response.text


class FakeAgentOrchestrator:
    def __init__(
        self,
        result: AgentRunResult,
        events: tuple[AgentRunEvent, ...] = (),
    ) -> None:
        self._result = result
        self._events = events
        self.last_request: AgentRunRequest | None = None

    def run(
        self,
        request: AgentRunRequest,
        event_sink: Any | None = None,
    ) -> AgentRunResult:
        self.last_request = request
        if event_sink is not None:
            for event in self._events:
                event_sink(event)
        return self._result


class FailingAgentOrchestrator:
    def __init__(self, error: Exception) -> None:
        self._error = error

    def run(self, request: AgentRunRequest) -> AgentRunResult:
        raise self._error


class FakeAgentFileResolver:
    def __init__(self, resolved_path: Path | None = None) -> None:
        self._resolved_path = resolved_path

    def resolve_file_path(
        self,
        session_id: str | None,
        file_id: str | None,
        direct_file_path: str | None,
    ) -> Path | None:
        if self._resolved_path is not None:
            return self._resolved_path
        return Path(direct_file_path) if direct_file_path else None


class FakeAgentFileUploadService:
    def __init__(self, result: AgentFileUploadResult) -> None:
        self._result = result
        self.last_source_path: Path | None = None
        self.last_original_filename: str | None = None

    def register_upload(
        self,
        source_path: Path,
        original_filename: str,
    ) -> AgentFileUploadResult:
        self.last_source_path = source_path
        self.last_original_filename = original_filename
        return self._result


class FailingAgentFileUploadService:
    def __init__(self, error: Exception) -> None:
        self._error = error

    def register_upload(
        self,
        source_path: Path,
        original_filename: str,
    ) -> AgentFileUploadResult:
        raise self._error


class LedgerAnalysisToolCallingModel:
    provider_name = "fake"

    def __init__(self) -> None:
        self.calls = 0

    def generate(self, request: ModelRequest) -> ModelResponse:
        self.calls += 1
        if self.calls == 1:
            target_path = _extract_target_path(request)
            return ModelResponse(
                text="",
                provider_name="fake",
                model_name="tool-caller",
                finish_reason="tool_calls",
                tool_calls=(
                    ToolCall(
                        name="analyze_ledger",
                        arguments={
                            "file_path": str(target_path),
                            "sheet_name": "Grand Livre",
                        },
                    ),
                ),
            )
        return ModelResponse(
            text="Le Grand Livre contient 4 lignes et 5 colonnes.",
            provider_name="fake",
            model_name="tool-caller",
            finish_reason="stop",
            tool_calls=(),
        )


def _extract_target_path(request: ModelRequest) -> Path:
    for message in request.messages:
        if message.content.startswith("Fichier cible: "):
            return Path(message.content.removeprefix("Fichier cible: "))
    raise AssertionError("target file path is required")


def _post(app: Any, path: str, json: dict[str, object]) -> httpx.Response:
    return asyncio.run(_async_post(app, path, json))


def _post_files(
    app: Any,
    path: str,
    files: dict[str, tuple[str, bytes, str]],
) -> httpx.Response:
    return asyncio.run(_async_post_files(app, path, files))


async def _async_post(
    app: Any,
    path: str,
    json: dict[str, object],
) -> httpx.Response:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        return await client.post(path, json=json)


async def _async_post_files(
    app: Any,
    path: str,
    files: dict[str, tuple[str, bytes, str]],
) -> httpx.Response:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        return await client.post(path, files=files)
