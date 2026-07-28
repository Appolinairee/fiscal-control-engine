from typing import Any

from pydantic import BaseModel, Field


class AgentRunHttpRequest(BaseModel):
    message: str = Field(min_length=1)
    file_path: str | None = None
    allowed_tools: list[str] = Field(default_factory=list)


class AgentToolResultResponse(BaseModel):
    tool_name: str
    ok: bool
    output: dict[str, Any]
    error_code: str | None = None
    error_message: str | None = None


class AgentRunResponse(BaseModel):
    answer: str
    tool_results: list[AgentToolResultResponse]
