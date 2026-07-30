from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, model_validator


class AgentRunHttpRequest(BaseModel):
    message: str = Field(min_length=1)
    file_path: str | None = None
    session_id: str | None = None
    file_id: str | None = None
    allowed_tools: list[str] = Field(default_factory=list)
    requested_tool: str | None = None
    sheet_name: str | None = None

    @model_validator(mode="after")
    def validate_file_reference(self) -> "AgentRunHttpRequest":
        has_direct_path = self.file_path is not None
        has_session_reference = self.session_id is not None or self.file_id is not None
        if has_direct_path and has_session_reference:
            raise ValueError("choose either file_path or session_id/file_id")
        if has_session_reference and not (self.session_id and self.file_id):
            raise ValueError("session_id and file_id are required together")
        return self


class AgentToolResultResponse(BaseModel):
    tool_name: str
    ok: bool
    output: dict[str, Any]
    error_code: str | None = None
    error_message: str | None = None


class AgentRunResponse(BaseModel):
    answer: str
    provider_name: str
    model_name: str
    tool_results: list[AgentToolResultResponse]


class AgentFileUploadResponse(BaseModel):
    session_id: str
    file_id: str
    original_filename: str
    expires_at: datetime
    validated_for_agent: bool
    rag_indexable: bool
    sheet_names: list[str]


class AgentErrorDetail(BaseModel):
    code: str
    message: str


class AgentErrorResponse(BaseModel):
    error: AgentErrorDetail
