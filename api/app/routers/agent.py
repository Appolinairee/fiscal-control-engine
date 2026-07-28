from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends

from app.agent.orchestrator import AgentOrchestrator, AgentRunRequest
from app.config import Settings, get_settings
from app.excel_agent.excel_tools import ExcelAgentTools
from app.excel_agent.tool_executor import ExcelToolExecutor
from app.excel_agent.tool_registry import create_excel_tool_registry
from app.llm.model_provider_factory import create_model_provider
from app.schemas.agent import (
    AgentRunHttpRequest,
    AgentRunResponse,
    AgentToolResultResponse,
)

DEFAULT_AGENT_TOOLS = ("list_sheets", "get_columns", "profile_sheet")

router = APIRouter(prefix="/agent", tags=["agent"])
SettingsDependency = Annotated[Settings, Depends(get_settings)]


def get_agent_orchestrator(settings: SettingsDependency) -> AgentOrchestrator:
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


AgentOrchestratorDependency = Annotated[
    AgentOrchestrator,
    Depends(get_agent_orchestrator),
]


@router.post("/runs", response_model=AgentRunResponse)
def run_agent(
    request: AgentRunHttpRequest,
    orchestrator: AgentOrchestratorDependency,
) -> AgentRunResponse:
    result = orchestrator.run(
        AgentRunRequest(
            user_message=request.message,
            file_path=Path(request.file_path) if request.file_path else None,
            allowed_tools=tuple(request.allowed_tools or DEFAULT_AGENT_TOOLS),
        ),
    )
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
