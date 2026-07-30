import json
from collections.abc import Iterator
from datetime import timedelta
from functools import lru_cache
from pathlib import Path
from queue import Queue
from tempfile import NamedTemporaryFile
from threading import Thread
from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile, status
from fastapi.responses import JSONResponse, StreamingResponse

from app.account_mapping.rule_loader import load_classification_rules
from app.agent.orchestrator import (
    AgentOrchestrator,
    AgentRunEvent,
    AgentRunRequest,
    AgentRunResult,
)
from app.agent_file.domain import (
    AgentFileExpiredError,
    AgentFileMissingError,
    AgentFileReadError,
    AgentFileTooLargeError,
    UnsupportedAgentFileError,
)
from app.agent_file.file_resolver import AgentFileResolver
from app.agent_file.persistent_file_store import PersistentAgentFileStore
from app.agent_file.temporary_file_store import TemporaryAgentFileStore
from app.agent_file.upload_service import AgentFileUploadService
from app.agent_file.upload_validator import AgentExcelUploadValidator
from app.agent_persistence.repository import SqlAlchemyAgentRepository
from app.config import Settings, get_settings
from app.database import Base, create_database_engine, create_session_factory
from app.excel_agent.excel_tools import ExcelAgentTools
from app.excel_agent.tool_executor import ExcelToolExecutor
from app.excel_agent.tool_registry import create_excel_tool_registry
from app.llm.domain import ToolCall
from app.llm.model_provider_factory import create_model_provider
from app.schemas.agent import (
    AgentErrorDetail,
    AgentErrorResponse,
    AgentFileUploadResponse,
    AgentRunEventResponse,
    AgentRunHttpRequest,
    AgentRunResponse,
    AgentToolResultResponse,
)

DEFAULT_AGENT_TOOLS = (
    "list_sheets",
    "get_columns",
    "profile_sheet",
    "classify_ledger_schema",
    "analyze_ledger",
    "aggregate_ledger",
    "query_ledger_entries",
    "calculate_ledger_metrics",
    "detect_data_quality_issues",
    "detect_tax_candidates",
)

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
            gemini_api_key=(
                settings.llm_gemini_api_key.get_secret_value()
                if settings.llm_gemini_api_key is not None
                else None
            ),
            gemini_base_url=settings.llm_gemini_base_url,
            groq_api_key=(
                settings.llm_groq_api_key.get_secret_value()
                if settings.llm_groq_api_key is not None
                else None
            ),
            groq_base_url=settings.llm_groq_base_url,
        )
        return AgentOrchestrator(
            model_provider=model_provider,
            tool_executor=ExcelToolExecutor(
                tools=ExcelAgentTools(
                    allowed_root=Path(settings.excel_agent_allowed_root_path),
                    allowed_roots=(Path(settings.agent_file_storage_root_path),),
                ),
                registry=create_excel_tool_registry(),
                tax_candidate_rules=load_classification_rules(
                    Path(settings.ras_classification_rules_path),
                ),
            ),
            max_answer_characters=settings.agent_max_answer_characters,
        )
    except ValueError as exc:
        raise AgentEndpointError(
            public_code="agent_configuration_error",
            public_message="La configuration agent est invalide.",
        ) from exc


@lru_cache
def _get_agent_repository(database_url: str) -> SqlAlchemyAgentRepository:
    engine = create_database_engine(database_url)
    Base.metadata.create_all(engine)
    return SqlAlchemyAgentRepository(session_factory=create_session_factory(engine))


async def get_agent_repository(
    settings: SettingsDependency,
) -> SqlAlchemyAgentRepository | None:
    if not settings.database_url:
        return None
    return _get_agent_repository(settings.database_url)


AgentRepositoryDependency = Annotated[
    SqlAlchemyAgentRepository | None,
    Depends(get_agent_repository),
]


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


async def get_agent_file_resolver(
    settings: SettingsDependency,
    repository: AgentRepositoryDependency,
) -> AgentFileResolver:
    store = _build_agent_file_store(settings=settings, repository=repository)
    return AgentFileResolver(store=store)


async def get_agent_file_upload_service(
    settings: SettingsDependency,
    repository: AgentRepositoryDependency,
) -> AgentFileUploadService:
    validator = AgentExcelUploadValidator(
        max_file_size_bytes=settings.agent_file_max_upload_bytes,
    )
    return AgentFileUploadService(
        store=_build_agent_file_store(
            settings=settings,
            repository=repository,
            upload_validator=validator,
        ),
        validator=validator,
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
    repository: AgentRepositoryDependency,
) -> AgentRunResponse | JSONResponse:
    try:
        file_path = file_resolver.resolve_file_path(
            session_id=request.session_id,
            file_id=request.file_id,
            direct_file_path=request.file_path,
        )
        result = orchestrator.run(
            _to_agent_run_request(
                request=request,
                file_path=file_path,
            ),
        )
        _save_agent_run_if_configured(
            request=request,
            result=result,
            repository=repository,
        )
    except AgentFileExpiredError:
        return _to_error_response(_file_expired_error())
    except AgentFileMissingError:
        return _to_error_response(_file_missing_error())
    except ValueError:
        return _to_error_response(_file_reference_error())
    except AgentEndpointError as exc:
        return _to_error_response(exc)
    return _to_agent_run_response(result)


@router.post(
    "/runs/stream",
    response_model=None,
    responses={400: {"model": AgentErrorResponse}},
)
async def stream_agent_run(
    request: AgentRunHttpRequest,
    orchestrator: AgentOrchestratorDependency,
    file_resolver: AgentFileResolverDependency,
    repository: AgentRepositoryDependency,
) -> StreamingResponse | JSONResponse:
    try:
        file_path = file_resolver.resolve_file_path(
            session_id=request.session_id,
            file_id=request.file_id,
            direct_file_path=request.file_path,
        )
        agent_request = _to_agent_run_request(
            request=request,
            file_path=file_path,
        )
    except AgentFileExpiredError:
        return _to_error_response(_file_expired_error())
    except AgentFileMissingError:
        return _to_error_response(_file_missing_error())
    except ValueError:
        return _to_error_response(_file_reference_error())

    return StreamingResponse(
        _stream_agent_run(orchestrator, agent_request, request, repository),
        media_type="application/x-ndjson",
    )


def _build_agent_file_store(
    settings: Settings,
    repository: SqlAlchemyAgentRepository | None,
    upload_validator: AgentExcelUploadValidator | None = None,
) -> TemporaryAgentFileStore | PersistentAgentFileStore:
    if repository is None:
        return _get_agent_file_store(
            storage_root_path=settings.agent_file_storage_root_path,
            ttl_seconds=settings.agent_file_ttl_seconds,
        )
    return PersistentAgentFileStore(
        storage_root=Path(settings.agent_file_storage_root_path),
        repository=repository,
        ttl=timedelta(seconds=settings.agent_file_ttl_seconds),
        upload_validator=upload_validator,
    )


def _to_agent_run_request(
    request: AgentRunHttpRequest,
    file_path: Path | None,
) -> AgentRunRequest:
    allowed_tools = _effective_allowed_tools(request.allowed_tools)
    return AgentRunRequest(
        user_message=request.message,
        file_path=file_path,
        sheet_name=request.sheet_name,
        allowed_tools=allowed_tools if file_path is not None else (),
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
    )


def _effective_allowed_tools(requested_tools: list[str]) -> tuple[str, ...]:
    if not requested_tools:
        return DEFAULT_AGENT_TOOLS
    return tuple(dict.fromkeys((*requested_tools, *DEFAULT_AGENT_TOOLS)))


def _save_agent_run_if_configured(
    request: AgentRunHttpRequest,
    result: AgentRunResult,
    repository: SqlAlchemyAgentRepository | None,
) -> None:
    if repository is None:
        return
    repository.save_run(
        user_message=request.message,
        result=result,
        session_id=request.session_id,
        file_id=request.file_id,
    )


def _file_reference_error() -> AgentEndpointError:
    return AgentEndpointError(
        public_code="agent_file_reference_error",
        public_message="La reference fichier agent est invalide.",
    )


def _file_missing_error() -> AgentEndpointError:
    return AgentEndpointError(
        public_code="file_missing",
        public_message="Le fichier agent est introuvable ou a ete supprime.",
    )


def _file_expired_error() -> AgentEndpointError:
    return AgentEndpointError(
        public_code="file_expired",
        public_message="Le fichier agent a expire. Veuillez le televerser a nouveau.",
    )


def _to_agent_run_response(result: AgentRunResult) -> AgentRunResponse:
    return AgentRunResponse(
        answer=result.answer,
        provider_name=result.provider_name,
        model_name=result.model_name,
        execution_events=[
            _to_agent_run_event_response(event)
            for event in result.execution_events
        ],
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


def _to_agent_run_event_response(event: AgentRunEvent) -> AgentRunEventResponse:
    return AgentRunEventResponse(
        event_type=event.event_type,
        title=event.title,
        message=event.message,
        status=event.status,
        tool_name=event.tool_name,
        provider_name=event.provider_name,
        model_name=event.model_name,
    )


def _stream_agent_run(
    orchestrator: AgentOrchestrator,
    request: AgentRunRequest,
    http_request: AgentRunHttpRequest,
    repository: SqlAlchemyAgentRepository | None,
) -> Iterator[str]:
    queue: Queue[object] = Queue()

    def run_worker() -> None:
        try:
            result = orchestrator.run(request, event_sink=queue.put)
            _save_agent_run_if_configured(
                request=http_request,
                result=result,
                repository=repository,
            )
            for answer_chunk in _split_answer_for_streaming(result.answer):
                queue.put(
                    AgentRunEvent(
                        event_type="answer_delta",
                        title="Réponse en cours",
                        message=answer_chunk,
                        status="streaming",
                        provider_name=result.provider_name,
                        model_name=result.model_name,
                    ),
                )
            queue.put(result)
        except Exception:
            queue.put(
                AgentRunEvent(
                    event_type="run_failed",
                    title="Analyse interrompue",
                    message="L'analyse n'a pas pu être terminée.",
                    status="error",
                ),
            )
        finally:
            queue.put(None)

    Thread(target=run_worker, daemon=True).start()

    while True:
        item = queue.get()
        if item is None:
            break
        if isinstance(item, AgentRunEvent):
            yield _to_ndjson_line(
                event_type="event",
                data=_to_agent_run_event_response(item).model_dump(),
            )
        if isinstance(item, AgentRunResult):
            yield _to_ndjson_line(
                event_type="result",
                data=_to_agent_run_response(item).model_dump(mode="json"),
            )


def _split_answer_for_streaming(answer: str) -> Iterator[str]:
    for chunk in (part.strip() for part in answer.splitlines()):
        if chunk:
            yield chunk


def _to_ndjson_line(event_type: str, data: dict[str, object]) -> str:
    return json.dumps(
        {"type": event_type, "data": data},
        ensure_ascii=False,
    ) + "\n"


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
