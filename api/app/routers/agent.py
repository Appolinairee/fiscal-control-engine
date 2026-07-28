from datetime import timedelta
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.agent.orchestrator import AgentOrchestrator, AgentRunRequest
from app.agent_file.file_resolver import AgentFileResolver
from app.agent_file.temporary_file_store import TemporaryAgentFileStore
from app.agent_file.upload_validator import AgentExcelUploadValidator
from app.config import Settings, get_settings
from app.excel_agent.excel_tools import ExcelAgentTools
from app.excel_agent.tool_executor import ExcelToolExecutor
from app.excel_agent.tool_registry import create_excel_tool_registry
from app.llm.model_provider_factory import create_model_provider
from app.schemas.agent import (
    AgentErrorDetail,
    AgentErrorResponse,
    AgentRunHttpRequest,
    AgentRunResponse,
    AgentToolResultResponse,
)

DEFAULT_AGENT_TOOLS = ("list_sheets", "get_columns", "profile_sheet")

router = APIRouter(prefix="/agent", tags=["agent"])
SettingsDependency = Annotated[Settings, Depends(get_settings)]


class AgentEndpointError(RuntimeError):
    def __init__(self, public_code: str, public_message: str) -> None:
        self.public_code = public_code
        self.public_message = public_message
        super().__init__(public_code)


def get_agent_orchestrator(settings: SettingsDependency) -> AgentOrchestrator:
    try:
        model_provider = create_model_provider(settings.llm_provider_chain)
        return AgentOrchestrator(
            model_provider=model_provider,
            tool_executor=ExcelToolExecutor(
                tools=ExcelAgentTools(
                    allowed_root=Path(settings.excel_agent_allowed_root_path),
                ),
                registry=create_excel_tool_registry(),
            ),
            max_answer_characters=settings.agent_max_answer_characters,
        )
    except ValueError as exc:
        raise AgentEndpointError(
            public_code="agent_configuration_error",
            public_message="La configuration agent est invalide.",
        ) from exc


def get_agent_file_resolver(settings: SettingsDependency) -> AgentFileResolver:
    store = TemporaryAgentFileStore(
        storage_root=Path(settings.agent_file_storage_root_path),
        ttl=timedelta(seconds=settings.agent_file_ttl_seconds),
        upload_validator=AgentExcelUploadValidator(
            max_file_size_bytes=settings.agent_file_max_upload_bytes,
        ),
    )
    return AgentFileResolver(store=store)


AgentOrchestratorDependency = Annotated[
    AgentOrchestrator,
    Depends(get_agent_orchestrator),
]
AgentFileResolverDependency = Annotated[
    AgentFileResolver,
    Depends(get_agent_file_resolver),
]


@router.post(
    "/runs",
    response_model=AgentRunResponse,
    responses={400: {"model": AgentErrorResponse}},
)
def run_agent(
    request: AgentRunHttpRequest,
    orchestrator: AgentOrchestratorDependency,
    file_resolver: AgentFileResolverDependency,
) -> AgentRunResponse | JSONResponse:
    try:
        file_path = file_resolver.resolve_file_path(
            session_id=request.session_id,
            file_id=request.file_id,
            direct_file_path=request.file_path,
        )
        result = orchestrator.run(
            AgentRunRequest(
                user_message=request.message,
                file_path=file_path,
                allowed_tools=tuple(request.allowed_tools or DEFAULT_AGENT_TOOLS),
            ),
        )
    except ValueError:
        return _to_error_response(
            AgentEndpointError(
                public_code="agent_file_reference_error",
                public_message="La reference fichier agent est invalide.",
            ),
        )
    except AgentEndpointError as exc:
        return _to_error_response(exc)
    return AgentRunResponse(
        answer=result.answer,
        tool_results=[
            AgentToolResultResponse(
                tool_name=tool_result.tool_name,
                ok=tool_result.ok,
                output=tool_result.output,
                error_code=tool_result.error_code,
                error_message=tool_result.error_message,
            )
            for tool_result in result.tool_results
        ],
    )


def _to_error_response(error: AgentEndpointError) -> JSONResponse:
    response = AgentErrorResponse(
        error=AgentErrorDetail(
            code=error.public_code,
            message=error.public_message,
        ),
    )
    return JSONResponse(status_code=400, content=response.model_dump())
