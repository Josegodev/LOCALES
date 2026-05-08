import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _validate_trace_id(value: str) -> str:
    trace_id = value.strip()
    try:
        parsed = uuid.UUID(trace_id)
    except ValueError as exc:
        raise ValueError("trace_id_invalid") from exc

    if trace_id not in {parsed.hex, str(parsed)}:
        raise ValueError("trace_id_invalid")

    return trace_id


class TraceContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    trace_id: str = Field(min_length=32, max_length=36)
    user_id: int | None = None
    chat_id: int | None = None

    @field_validator("trace_id")
    @classmethod
    def validate_trace_id(cls, value: str) -> str:
        return _validate_trace_id(value)


class TelegramMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chat_id: int
    user_id: int | None = None
    text: str = ""


class ParsedDocCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    command: Literal["doc.create"] = "doc.create"
    filename: str = Field(min_length=1, max_length=120)
    content: str
    user_id: int
    chat_id: int


class ParsedDocAiCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    command: Literal["doc_ai.create"] = "doc_ai.create"
    filename: str = Field(min_length=1, max_length=120)
    prompt: str
    user_id: int
    chat_id: int
