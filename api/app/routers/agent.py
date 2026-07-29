from datetime import timedelta
from functools import lru_cache
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile, status
from fastapi.responses import JSONResponse

from app.agent.orchestrator import AgentOrchestrator, AgentRunRequest
from app.agent_file.domain import (
    AgentFileReadError,
    AgentFileTooLargeError,
    UnsupportedAgentFileError,
)
from app.agent_file.file_resolver import AgentFileResolver
from app.agent_file.temporary_file_store import TemporaryAgentFileStore
from app.agent_file.upload_service import AgentFileUploadService
from app.agent_file.upload_validator import AgentExcelUploadValidator
from app.config import Settings, get_settings
from app.excel_agent.excel_tools import ExcelAgentTools
from app.excel_agent.tool_executor import ExcelToolExecutor
from app.excel_agent.tool_registry import create_excel_tool_registry
from app.llm.domain import ToolCall
from app.llm.model_provider_factory import create_model_provider
from app.schemas.agent import (
    AgentErrorDetail,
    AgentErrorResponse,
    AgentFileUploadResponse,
    AgentRunHttpRequest,
    AgentRunResponse,
    AgentToolResultResponse,
)

DEFAULT_AGENT_TOOLS = ("list_sheets", "get_columns", "profile_sheet", "analyze_ledger")

router = APIRouter(prefix="/agent", tags=["agent"])


async def get_api_settings() -> Settings:
    return get_settings()


SettingsDependency = Annotated[Settings, Depends(get_api_settings)]


class AgentEndpointError(RuntimeError):
    def __init__(self, public_code: str, public_message: str) -> None:
        self.public_code = public_code
        self.public_message = public_message
        super().__init__(public_code)


async def get_agent_orchestrator(settings: SettingsDependency) -> AgentOrchestrator:
    try:
        model_provider = create_model_provider(
            provider_chain=settings.llm_provider_chain,
            openai_compatible_api_key=(
                settings.llm_openai_compatible_api_key.get_secret_value()
                if settings.llm_openai_compatible_api_key is not None
                else None
            ),
            openai_compatible_base_url=settings.llm_openai_compatible_base_url,
        )
        return AgentOrchestrator(
            model_provider=model_provider,
            tool_executor=ExcelToolExecutor(
                tools=ExcelAgentTools(
                    allowed_root=Path(settings.excel_agent_allowed_root_path),
                    allowed_roots=(Path(settings.agent_file_storage_root_path),),
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


@lru_cache
def _get_agent_file_store(
    storage_root_path: str,
    ttl_seconds: int,
) -> TemporaryAgentFileStore:
    return TemporaryAgentFileStore(
        storage_root=Path(storage_root_path),
        ttl=timedelta(seconds=ttl_seconds),
    )


async def get_agent_file_store(settings: SettingsDependency) -> TemporaryAgentFileStore:
    return _get_agent_file_store(
        storage_root_path=settings.agent_file_storage_root_path,
        ttl_seconds=settings.agent_file_ttl_seconds,
    )


AgentFileStoreDependency = Annotated[
    TemporaryAgentFileStore,
    Depends(get_agent_file_store),
]


async def get_agent_file_resolver(
    store: AgentFileStoreDependency,
) -> AgentFileResolver:
    return AgentFileResolver(store=store)


async def get_agent_file_upload_service(
    settings: SettingsDependency,
    store: AgentFileStoreDependency,
) -> AgentFileUploadService:
    return AgentFileUploadService(
        store=store,
        validator=AgentExcelUploadValidator(
            max_file_size_bytes=settings.agent_file_max_upload_bytes,
        ),
    )


AgentOrchestratorDependency = Annotated[
    AgentOrchestrator,
    Depends(get_agent_orchestrator),
]
AgentFileResolverDependency = Annotated[
    AgentFileResolver,
    Depends(get_agent_file_resolver),
]
AgentFileUploadServiceDependency = Annotated[
    AgentFileUploadService,
    Depends(get_agent_file_upload_service),
]


async def _copy_upload_to_temporary_file(
    uploaded_file: UploadFile,
    max_upload_bytes: int,
) -> Path:
    source_suffix = Path(uploaded_file.filename or "").suffix
    with NamedTemporaryFile(
        prefix="agent-upload-",
        suffix=source_suffix,
        delete=False,
    ) as temporary_file:
        temporary_path = Path(temporary_file.name)
        written_bytes = 0
        while chunk := await uploaded_file.read(1024 * 1024):
            written_bytes += len(chunk)
            if written_bytes > max_upload_bytes:
                temporary_path.unlink(missing_ok=True)
                raise AgentFileTooLargeError("agent file is too large")
            temporary_file.write(chunk)
    return temporary_path


@router.post(
    "/files",
    response_model=AgentFileUploadResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": AgentErrorResponse},
        413: {"model": AgentErrorResponse},
    },
)
async def upload_agent_file(
    settings: SettingsDependency,
    upload_service: AgentFileUploadServiceDependency,
    file: Annotated[UploadFile, File()],
) -> AgentFileUploadResponse | JSONResponse:
    temporary_path: Path | None = None
    try:
        temporary_path = await _copy_upload_to_temporary_file(
            uploaded_file=file,
            max_upload_bytes=settings.agent_file_max_upload_bytes,
        )
        result = upload_service.register_upload(
            source_path=temporary_path,
            original_filename=file.filename or "",
        )
    except AgentFileTooLargeError:
        return _to_error_response(
            AgentEndpointError(
                public_code="agent_file_too_large",
                public_message="Le fichier Excel agent depasse la taille autorisee.",
            ),
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        )
    except UnsupportedAgentFileError:
        return _to_error_response(
            AgentEndpointError(
                public_code="agent_file_unsupported",
                public_message="Le format du fichier agent n'est pas supporte.",
            ),
        )
    except AgentFileReadError:
        return _to_error_response(
            AgentEndpointError(
                public_code="agent_file_invalid",
                public_message="Le fichier Excel agent est invalide ou illisible.",
            ),
        )
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        await file.close()

    return AgentFileUploadResponse(
        session_id=result.session_id,
        file_id=result.file_id,
        original_filename=result.original_filename,
        expires_at=result.expires_at,
        validated_for_agent=result.validated_for_agent,
        rag_indexable=result.rag_indexable,
        sheet_names=list(result.sheet_names),
    )


@router.post(
    "/runs",
    response_model=AgentRunResponse,
    responses={400: {"model": AgentErrorResponse}},
)
async def run_agent(
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
                direct_tool_call=(
                    ToolCall(
                        name=request.requested_tool,
                        arguments={
                            "file_path": str(file_path),
                            "sheet_name": request.sheet_name,
                        },
                    )
                    if request.requested_tool and request.sheet_name and file_path
                    else None
                ),
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


def _to_error_response(
    error: AgentEndpointError,
    status_code: int = status.HTTP_400_BAD_REQUEST,
) -> JSONResponse:
    response = AgentErrorResponse(
        error=AgentErrorDetail(
            code=error.public_code,
            message=error.public_message,
        ),
    )
    return JSONResponse(status_code=status_code, content=response.model_dump())
