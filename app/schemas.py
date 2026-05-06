import uuid
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    model: str | None = None
    max_tokens: int | None = Field(default=None, ge=1, le=2048)
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    top_k: int | None = Field(default=3, ge=1, le=10)

class ChatResponse(BaseModel):
    status: str
    model: str
    answer: str
    latency_ms: int

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
