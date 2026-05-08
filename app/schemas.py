import math
import uuid
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    provider: str | None = None
    model: str | None = None
    max_tokens: int | None = Field(default=None, ge=1, le=2048)
    temperature: float = Field(default=0.2, ge=0.0, le=1.0)
    use_rag: bool = True
    top_k: int | None = Field(default=3, ge=1, le=10)
    trace_id: str | None = Field(default=None, min_length=32, max_length=36)
    user_id: int | None = None
    chat_id: int | None = None

    @field_validator("trace_id")
    @classmethod
    def validate_trace_id(cls, value: str | None) -> str | None:
        if value is None:
            return value

        trace_id = value.strip()
        try:
            parsed = uuid.UUID(trace_id)
        except ValueError as exc:
            raise ValueError("trace_id_invalid") from exc

        if trace_id not in {parsed.hex, str(parsed)}:
            raise ValueError("trace_id_invalid")

        return trace_id

    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("temperature_invalid")
        return value

class ChatResponse(BaseModel):
    status: str
    provider: str
    model: str
    temperature: float = 0.2
    temperature_ignored: bool = False
    use_rag: bool = True
    answer: str
    latency_ms: int
    retrieval_status: str | None = None
    chunks: list[str] = Field(default_factory=list)
    chunk_ids: list[int] = Field(default_factory=list)
    prompt_eval_count: int | None = None
    eval_count: int | None = None
    prompt_eval_duration: int | None = None
    eval_duration: int | None = None
    total_duration: int | None = None
    load_duration: int | None = None

class ErrorResponse(BaseModel):
    status: str
    code: str
    message: str

class CreateDocumentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str = Field(min_length=32, max_length=36)
    filename: str = Field(min_length=1, max_length=120)
    content: str = Field(max_length=100_000)
    overwrite: Literal[False] = False
    user_id: int
    chat_id: int

    @field_validator("request_id")
    @classmethod
    def validate_request_id(cls, value: str) -> str:
        request_id = value.strip()
        try:
            parsed = uuid.UUID(request_id)
        except ValueError as exc:
            raise ValueError("request_id_invalid") from exc

        if request_id not in {parsed.hex, str(parsed)}:
            raise ValueError("request_id_invalid")

        return request_id

    @field_validator("filename")
    @classmethod
    def validate_filename(cls, value: str) -> str:
        filename = value.strip()

        if not filename:
            raise ValueError("filename_required")
        if Path(filename).is_absolute():
            raise ValueError("absolute_path_not_allowed")
        if ".." in filename:
            raise ValueError("parent_directory_not_allowed")
        if "/" in filename or "\\" in filename:
            raise ValueError("path_separator_not_allowed")
        if Path(filename).suffix.lower() != ".md":
            raise ValueError("only_markdown_extension_allowed")

        return filename

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("content_required")
        return value


class DocumentCreateResponse(BaseModel):
    request_id: str
    status: str
    filename: str
    path: str
    chars: int
    created_at: str


DocumentCreateRequest = CreateDocumentRequest
