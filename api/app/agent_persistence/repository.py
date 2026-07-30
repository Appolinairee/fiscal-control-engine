from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from sqlalchemy import desc, select
from sqlalchemy.orm import Session, sessionmaker

from app.agent.orchestrator import AgentRunResult
from app.agent_file.domain import StoredAgentFile
from app.agent_persistence.models import (
    AgentFileModel,
    AgentMessageModel,
    AgentRunEventModel,
    AgentRunModel,
    AgentSessionModel,
    AgentToolResultModel,
)


@dataclass(frozen=True)
class AgentConversationSummary:
    run_id: str
    session_id: str | None
    file_id: str | None
    title: str
    status: str
    created_at: datetime


@dataclass(frozen=True)
class AgentFileSummary:
    session_id: str
    file_id: str
    original_filename: str
    file_size_bytes: int | None
    sheet_names: tuple[str, ...]
    created_at: datetime
    expires_at: datetime
    status: str


@dataclass(frozen=True)
class AgentRunEventSummary:
    event_type: str
    title: str
    message: str
    status: str
    tool_name: str | None
    provider_name: str | None
    model_name: str | None
    created_at: datetime


class SqlAlchemyAgentRepository:
    def __init__(
        self,
        session_factory: sessionmaker[Session],
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._now = now or (lambda: datetime.now(tz=UTC))

    def save_file(
        self,
        stored_file: StoredAgentFile,
        file_size_bytes: int,
        sheet_names: tuple[str, ...],
        mime_type: str | None = None,
    ) -> None:
        with self._session_factory() as session:
            now = self._now()
            existing_session = session.get(AgentSessionModel, stored_file.session_id)
            if existing_session is None:
                session.add(
                    AgentSessionModel(
                        session_id=stored_file.session_id,
                        created_at=now,
                        expires_at=stored_file.expires_at,
                        status="active",
                        active_file_id=stored_file.file_id,
                    ),
                )
                session.flush()
            else:
                existing_session.active_file_id = stored_file.file_id
                existing_session.expires_at = max(
                    _as_utc(existing_session.expires_at),
                    stored_file.expires_at,
                )
            session.add(
                AgentFileModel(
                    file_id=stored_file.file_id,
                    session_id=stored_file.session_id,
                    original_filename=stored_file.original_filename,
                    stored_path=str(stored_file.path),
                    mime_type=mime_type,
                    file_size_bytes=file_size_bytes,
                    sheet_names=list(sheet_names),
                    created_at=now,
                    expires_at=stored_file.expires_at,
                    validated_for_agent=stored_file.validated_for_agent,
                    anonymized_for_rag=stored_file.anonymized_for_rag,
                    rag_indexable=stored_file.rag_indexable,
                    status="active",
                ),
            )
            session.commit()

    def find_file(self, session_id: str, file_id: str) -> StoredAgentFile | None:
        with self._session_factory() as session:
            file_model = session.scalar(
                select(AgentFileModel).where(
                    AgentFileModel.session_id == session_id,
                    AgentFileModel.file_id == file_id,
                    AgentFileModel.status == "active",
                ),
            )
            if file_model is None:
                return None
            return StoredAgentFile(
                session_id=file_model.session_id,
                file_id=file_model.file_id,
                original_filename=file_model.original_filename,
                path=Path(file_model.stored_path),
                expires_at=_as_utc(file_model.expires_at),
                validated_for_agent=file_model.validated_for_agent,
                anonymized_for_rag=file_model.anonymized_for_rag,
                rag_indexable=file_model.rag_indexable,
            )

    def save_run(
        self,
        user_message: str,
        result: AgentRunResult,
        session_id: str | None = None,
        file_id: str | None = None,
    ) -> str:
        run_id = uuid4().hex
        now = self._now()
        with self._session_factory() as session:
            session.add(
                AgentRunModel(
                    run_id=run_id,
                    session_id=session_id,
                    file_id=file_id,
                    user_message=user_message,
                    answer=result.answer,
                    provider_name=result.provider_name,
                    model_name=result.model_name,
                    created_at=now,
                ),
            )
            session.flush()
            session.add(
                AgentMessageModel(
                    message_id=uuid4().hex,
                    run_id=run_id,
                    role="user",
                    content=user_message,
                    created_at=now,
                ),
            )
            session.add(
                AgentMessageModel(
                    message_id=uuid4().hex,
                    run_id=run_id,
                    role="assistant",
                    content=result.answer,
                    created_at=now,
                ),
            )
            for sequence, event in enumerate(result.execution_events):
                session.add(
                    AgentRunEventModel(
                        event_id=uuid4().hex,
                        run_id=run_id,
                        sequence=sequence,
                        event_type=event.event_type,
                        title=event.title,
                        message=event.message,
                        status=event.status,
                        tool_name=event.tool_name,
                        provider_name=event.provider_name,
                        model_name=event.model_name,
                        created_at=now,
                    ),
                )
            for sequence, tool_result in enumerate(result.tool_results):
                session.add(
                    AgentToolResultModel(
                        tool_result_id=uuid4().hex,
                        run_id=run_id,
                        sequence=sequence,
                        tool_name=tool_result.tool_name,
                        ok=tool_result.ok,
                        output=tool_result.output,
                        error_code=tool_result.error_code,
                        error_message=tool_result.error_message,
                        created_at=now,
                    ),
                )
            session.commit()
        return run_id

    def list_recent_conversations(
        self,
        limit: int = 20,
    ) -> tuple[AgentConversationSummary, ...]:
        safe_limit = min(max(1, limit), 50)
        with self._session_factory() as session:
            runs = session.scalars(
                select(AgentRunModel)
                .order_by(desc(AgentRunModel.created_at))
                .limit(safe_limit),
            ).all()
            return tuple(
                AgentConversationSummary(
                    run_id=run.run_id,
                    session_id=run.session_id,
                    file_id=run.file_id,
                    title=_title_from_message(run.user_message),
                    status=_conversation_status(run.provider_name),
                    created_at=_as_utc(run.created_at),
                )
                for run in runs
            )

    def list_recent_files(
        self,
        limit: int = 20,
    ) -> tuple[AgentFileSummary, ...]:
        safe_limit = min(max(1, limit), 50)
        with self._session_factory() as session:
            files = session.scalars(
                select(AgentFileModel)
                .where(AgentFileModel.status == "active")
                .order_by(desc(AgentFileModel.created_at))
                .limit(safe_limit),
            ).all()
            return tuple(
                AgentFileSummary(
                    session_id=file.session_id,
                    file_id=file.file_id,
                    original_filename=file.original_filename,
                    file_size_bytes=file.file_size_bytes,
                    sheet_names=tuple(str(sheet) for sheet in file.sheet_names),
                    created_at=_as_utc(file.created_at),
                    expires_at=_as_utc(file.expires_at),
                    status=file.status,
                )
                for file in files
            )

    def get_active_file(self, session_id: str) -> AgentFileSummary | None:
        with self._session_factory() as session:
            session_model = session.get(AgentSessionModel, session_id)
            if session_model is None or session_model.active_file_id is None:
                return None
            file_model = session.scalar(
                select(AgentFileModel).where(
                    AgentFileModel.session_id == session_id,
                    AgentFileModel.file_id == session_model.active_file_id,
                    AgentFileModel.status == "active",
                ),
            )
            if file_model is None:
                return None
            return _to_file_summary(file_model)

    def list_session_files(
        self,
        session_id: str,
        limit: int = 20,
    ) -> tuple[AgentFileSummary, ...]:
        safe_limit = min(max(1, limit), 50)
        with self._session_factory() as session:
            session_model = session.get(AgentSessionModel, session_id)
            active_file_id = (
                session_model.active_file_id if session_model is not None else None
            )
            files = session.scalars(
                select(AgentFileModel)
                .where(
                    AgentFileModel.session_id == session_id,
                    AgentFileModel.status == "active",
                )
                .order_by(
                    desc(AgentFileModel.file_id == active_file_id),
                    desc(AgentFileModel.created_at),
                )
                .limit(safe_limit),
            ).all()
            return tuple(_to_file_summary(file) for file in files)

    def list_recent_session_events(
        self,
        session_id: str,
        limit: int = 8,
    ) -> tuple[AgentRunEventSummary, ...]:
        safe_limit = min(max(1, limit), 20)
        with self._session_factory() as session:
            events = session.execute(
                select(AgentRunEventModel)
                .join(AgentRunModel, AgentRunEventModel.run_id == AgentRunModel.run_id)
                .where(AgentRunModel.session_id == session_id)
                .order_by(desc(AgentRunEventModel.created_at))
                .limit(safe_limit),
            ).scalars()
            return tuple(
                AgentRunEventSummary(
                    event_type=event.event_type,
                    title=event.title,
                    message=event.message,
                    status=event.status,
                    tool_name=event.tool_name,
                    provider_name=event.provider_name,
                    model_name=event.model_name,
                    created_at=_as_utc(event.created_at),
                )
                for event in events
            )


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _title_from_message(message: str) -> str:
    title = " ".join(message.split())
    if len(title) <= 64:
        return title
    return f"{title[:61].rstrip()}..."


def _conversation_status(provider_name: str) -> str:
    if provider_name in {"internal", "internal-fallback"}:
        return "Analyse interne"
    return "Réponse agent"


def _to_file_summary(file: AgentFileModel) -> AgentFileSummary:
    return AgentFileSummary(
        session_id=file.session_id,
        file_id=file.file_id,
        original_filename=file.original_filename,
        file_size_bytes=file.file_size_bytes,
        sheet_names=tuple(str(sheet) for sheet in file.sheet_names),
        created_at=_as_utc(file.created_at),
        expires_at=_as_utc(file.expires_at),
        status=file.status,
    )
