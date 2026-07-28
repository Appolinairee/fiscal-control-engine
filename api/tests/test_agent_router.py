from pathlib import Path

from fastapi.testclient import TestClient

from app.agent.orchestrator import AgentRunRequest, AgentRunResult
from app.excel_agent.domain import ToolExecutionResult
from app.main import create_app
from app.routers.agent import AgentEndpointError, get_agent_orchestrator


def test_agent_run_endpoint_returns_orchestrated_answer() -> None:
    app = create_app()
    fake_orchestrator = FakeAgentOrchestrator(
        AgentRunResult(
            answer="Le fichier contient 4 lignes et 5 colonnes.",
            tool_results=(
                ToolExecutionResult(
                    tool_name="profile_sheet",
                    ok=True,
                    output={"sheet_name": "Grand Livre", "row_count": 4},
                ),
            ),
        ),
    )
    app.dependency_overrides[get_agent_orchestrator] = lambda: fake_orchestrator
    client = TestClient(app)

    response = client.post(
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
        allowed_tools=("profile_sheet",),
    )


def test_agent_run_endpoint_validates_message() -> None:
    client = TestClient(create_app())

    response = client.post(
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
    app.dependency_overrides[get_agent_orchestrator] = lambda: fake_orchestrator
    client = TestClient(app)

    response = client.post(
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


def test_agent_run_endpoint_returns_sanitized_configuration_error() -> None:
    app = create_app()

    def fail_dependency() -> None:
        raise AgentEndpointError(
            public_code="agent_configuration_error",
            public_message="La configuration agent est invalide.",
        )

    app.dependency_overrides[get_agent_orchestrator] = fail_dependency
    client = TestClient(app)

    response = client.post(
        "/api/agent/runs",
        json={"message": "Analyse", "allowed_tools": ["profile_sheet"]},
    )

    assert response.status_code == 400
    assert response.json() == {
        "error": {
            "code": "agent_configuration_error",
            "message": "La configuration agent est invalide.",
        },
    }


def test_agent_tools_are_not_exposed_as_individual_http_endpoints() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/agent/tools/profile_sheet",
        json={"file_path": "grand_livre_minifie.xlsx"},
    )

    assert response.status_code == 404


class FakeAgentOrchestrator:
    def __init__(self, result: AgentRunResult) -> None:
        self._result = result
        self.last_request: AgentRunRequest | None = None

    def run(self, request: AgentRunRequest) -> AgentRunResult:
        self.last_request = request
        return self._result


class FailingAgentOrchestrator:
    def __init__(self, error: Exception) -> None:
        self._error = error

    def run(self, request: AgentRunRequest) -> AgentRunResult:
        raise self._error
