from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select
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
                    ),
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


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
