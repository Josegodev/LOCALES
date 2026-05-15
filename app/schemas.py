import math
import uuid
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CreateDocumentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str = Field(min_length=32, max_length=36)
    filename: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1, max_length=100_000)
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
        if Path(filename).is_absolute() or ".." in filename or "/" in filename or "\\" in filename:
            raise ValueError("filename_invalid")
        if Path(filename).suffix.lower() != ".md":
            raise ValueError("filename_extension_invalid")
        return filename

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("content_required")
        return value


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
    allowed_source_filenames: list[str] = Field(default_factory=list)
    active_document_id: int | None = Field(default=None, ge=1)
    active_document_title: str | None = Field(default=None, min_length=1, max_length=255)
    active_corpus: str | None = Field(default=None, min_length=1, max_length=64)
    last_source_intent: str | None = Field(default=None, min_length=1, max_length=64)

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

    @field_validator("allowed_source_filenames")
    @classmethod
    def validate_allowed_source_filenames(cls, value: list[str]) -> list[str]:
        normalized_filenames: list[str] = []

        for item in value:
            filename = Path(item.strip()).name
            if not filename:
                raise ValueError("allowed_source_filename_invalid")
            if filename not in normalized_filenames:
                normalized_filenames.append(filename)

        return normalized_filenames

class ChatResponse(BaseModel):
    trace_id: str | None = None
    status: str
    provider: str
    model: str
    temperature: float = 0.2
    temperature_ignored: bool = False
    use_rag: bool = True
    answer: str
    latency_ms: int
    retrieval_status: str | None = None
    answer_mode: str | None = None
    query_original: str | None = None
    query_normalized: str | None = None
    query_terms: list[str] = Field(default_factory=list)
    quoted_terms: list[str] = Field(default_factory=list)
    source_intent: str | None = None
    selected_corpus: str | None = None
    active_document_id: int | None = None
    active_document_title: str | None = None
    active_context_used: bool = False
    active_context_reason: str | None = None
    evidence_used: bool = False
    fallback_used: bool = False
    query_expansion_used: bool = False
    query_expansion_reason: str | None = None
    expanded_query_terms: list[str] = Field(default_factory=list)
    candidate_filenames: list[str] = Field(default_factory=list)
    selected_filenames: list[str] = Field(default_factory=list)
    chunks: list[str] = Field(default_factory=list)
    chunk_ids: list[int] = Field(default_factory=list)
    document_ids: list[int] = Field(default_factory=list)
    source_filenames: list[str] = Field(default_factory=list)
    scores: list[int] = Field(default_factory=list)
    warnings: list[str | dict] = Field(default_factory=list)
    prompt_eval_count: int | None = None
    eval_count: int | None = None
    prompt_eval_duration: int | None = None
    eval_duration: int | None = None
    total_duration: int | None = None
    load_duration: int | None = None


class ChatModelOption(BaseModel):
    provider: str
    model: str
    label: str
    is_default: bool = False


class ChatModelListResponse(BaseModel):
    status: str
    items: list[ChatModelOption] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    status: str
    code: str
    message: str

class ChatRunResponse(BaseModel):
    version: str | None = None
    trace_id: str | None = None
    created_at: str | None = None
    timestamp: str | None = None
    source: str | None = None
    endpoint: str | None = None
    input: str | None = None
    response: str | None = None
    provider: str | None = None
    model: str | None = None
    status: str | None = None
    retrieval_status: str | None = None
    chunk_ids: list[int] = Field(default_factory=list)
    document_ids: list[int] = Field(default_factory=list)
    source_filenames: list[str] = Field(default_factory=list)
    tokens_input: float | None = None
    tokens_output: float | None = None
    tokens_total: float | None = None
    latency_ms: float | None = None
    error_code: str | None = None
    error_message: str | None = None
    warnings: list[str] = Field(default_factory=list)
    use_rag: bool | None = None
    evidence_used: bool | None = None
    fallback_used: bool | None = None
    answer_mode: str | None = None


class ChatTraceResponse(ChatRunResponse):
    pass


class ChatRunListResponse(BaseModel):
    status: str
    items: list[ChatRunResponse] = Field(default_factory=list)
    count: int


class ChatTraceListResponse(BaseModel):
    status: str
    items: list[ChatTraceResponse] = Field(default_factory=list)
    count: int


class ChatTraceResetResponse(BaseModel):
    status: str
    removed_count: int


class ChatEvalListResponse(BaseModel):
    items: list[ChatTraceResponse] = Field(default_factory=list)
    count: int
    limit: int


class ChatSavedRunResponse(ChatTraceResponse):
    pass


class ChatRunsStatsResponse(BaseModel):
    total_runs: int
    ok_runs: int
    error_runs: int
    models: dict[str, int] = Field(default_factory=dict)
    avg_latency_ms: float | None = None
    avg_tokens_total: float | None = None
    runs: list[ChatSavedRunResponse] = Field(default_factory=list)


class ChatEvalFailure(BaseModel):
    name: str
    expected: Any = None
    actual: Any = None


class ChatEvalResultResponse(BaseModel):
    case_id: str | None = None
    status: str
    chat_status: str | None = None
    passed: bool
    failures: list[ChatEvalFailure] = Field(default_factory=list)
    retrieval_status: str | None = None
    source_filenames: list[str] = Field(default_factory=list)
    chunk_ids: list[int] = Field(default_factory=list)
    latency_ms: float | None = None
    response_preview: str = ""
    error_code: str | None = None
    error_message: str | None = None


class ChatEvalRunSummary(BaseModel):
    total: int
    passed: int
    failed: int
    errors: int
    pass_rate: float


class ChatEvalSavedRunItem(BaseModel):
    run_id: str | None = None
    created_at: str | None = None
    source: str | None = None
    cases_file: str | None = None
    baseline_file: str | None = None
    summary: ChatEvalRunSummary
    run_path: str | None = None


class ChatEvalRunsListResponse(BaseModel):
    status: str
    total_runs: int
    total_cases: int
    total_passed: int
    total_failed: int
    avg_pass_rate: float
    items: list[ChatEvalSavedRunItem] = Field(default_factory=list)


class ChatEvalRunResponse(BaseModel):
    status: str
    run_id: str
    run_path: str
    source: str
    cases_file: str
    baseline_file: str
    summary: ChatEvalRunSummary
    results: list[ChatEvalResultResponse] = Field(default_factory=list)
