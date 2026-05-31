import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
import re
from typing import Any

from pydantic import BaseModel, Field

from app.config import settings
from app.observability.logging import log_event
from app.schemas import normalize_temperature, normalize_top_p


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CHAT_RUNS_PATH = REPO_ROOT / "CHAT_RUNS"
CHAT_RUN_SOURCES = {"frontend", "chat"}
CHAT_RUN_ENDPOINT = "/chat"
CHAT_RUN_VERSION = "chat_run.v1"
CHAT_RUN_FILE_SUFFIX = ".json"


def _utc_timestamp(created_at: datetime | None = None) -> datetime:
    timestamp = created_at or datetime.now(timezone.utc)
    if timestamp.tzinfo is None:
        return timestamp.replace(tzinfo=timezone.utc)
    return timestamp.astimezone(timezone.utc)


def _nullable_str(value: Any) -> str | None:
    return value if isinstance(value, str) else None


def _nullable_number(value: Any) -> int | float | None:
    if isinstance(value, bool):
        return None
    return value if isinstance(value, (int, float)) else None


def _nullable_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def _nullable_temperature(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return normalize_temperature(value)
    except (TypeError, ValueError):
        return None


def _nullable_top_p(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return normalize_top_p(value)
    except (TypeError, ValueError):
        return None


def _normalized_generation_config(
    record: dict[str, Any],
    temperature: float | None,
    top_p: float | None,
    max_tokens: int | None,
) -> dict[str, int | float] | None:
    raw_generation_config = record.get("generation_config")
    normalized_config: dict[str, int | float] = {}
    if isinstance(raw_generation_config, dict):
        configured_temperature = _nullable_temperature(raw_generation_config.get("temperature"))
        if configured_temperature is not None:
            normalized_config["temperature"] = configured_temperature
        configured_top_p = _nullable_top_p(raw_generation_config.get("top_p"))
        if configured_top_p is not None:
            normalized_config["top_p"] = configured_top_p
        configured_max_tokens = _nullable_int(raw_generation_config.get("max_tokens"))
        if configured_max_tokens is not None:
            normalized_config["max_tokens"] = configured_max_tokens

    if temperature is not None and "temperature" not in normalized_config:
        normalized_config["temperature"] = temperature
    if top_p is not None and "top_p" not in normalized_config:
        normalized_config["top_p"] = top_p
    if max_tokens is not None and "max_tokens" not in normalized_config:
        normalized_config["max_tokens"] = max_tokens

    return normalized_config or None


def _int_list(value: Any) -> list[int]:
    if not isinstance(value, list):
        return []
    output: list[int] = []
    for item in value:
        if isinstance(item, int):
            output.append(item)
        elif isinstance(item, str) and item.isdigit():
            output.append(int(item))
    return output


def _str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _warnings_list(value: Any) -> list[str]:
    return _str_list(value)


def _normalize_source(value: Any) -> str:
    if isinstance(value, str) and value in CHAT_RUN_SOURCES:
        return value
    return "chat"


def _normalize_endpoint(value: Any) -> str:
    if isinstance(value, str) and value.strip():
        return value
    return CHAT_RUN_ENDPOINT


def _normalize_retrieval_status(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    if not normalized or normalized == "unknown":
        return None
    return normalized


def _normalize_tokens_total(
    *,
    record: dict[str, Any],
    tokens_input: int | float | None,
    tokens_output: int | float | None,
) -> int | float | None:
    tokens_total = _nullable_number(record.get("tokens_total"))
    if tokens_total is not None:
        return tokens_total
    if tokens_input is None or tokens_output is None:
        return None
    return tokens_input + tokens_output


def _normalize_output_tokens_per_second(
    *,
    record: dict[str, Any],
    tokens_output: int | float | None,
) -> int | float | None:
    output_tokens_per_second = _nullable_number(record.get("output_tokens_per_second"))
    if output_tokens_per_second is not None:
        return output_tokens_per_second

    eval_duration = _nullable_number(record.get("eval_duration"))
    if tokens_output is None or eval_duration is None or eval_duration <= 0:
        return None

    return round(float(tokens_output) / (float(eval_duration) / 1_000_000_000), 4)


def resolve_chat_runs_path(path: Path | None = None) -> Path:
    def normalize_directory(candidate: Path) -> Path:
        if candidate.suffix.lower() in {".json", ".jsonl"}:
            return candidate.parent / candidate.stem
        return candidate

    if path is not None:
        return normalize_directory(path)

    for env_name in ("CHAT_RUNS_DIR", "CHAT_RUNS_PATH", "CHAT_RUNS", "CHAT_TRACE_PATH"):
        raw_value = os.getenv(env_name)
        if isinstance(raw_value, str) and raw_value.strip():
            candidate = Path(raw_value.strip())
            if not candidate.is_absolute():
                candidate = REPO_ROOT / candidate
            return normalize_directory(candidate)

    configured = getattr(settings, "chat_runs_path", None)
    if isinstance(configured, str) and configured.strip():
        candidate = Path(configured.strip())
        if not candidate.is_absolute():
            candidate = REPO_ROOT / candidate
        return normalize_directory(candidate)

    return DEFAULT_CHAT_RUNS_PATH


class ChatRunRecord(BaseModel):
    version: str = CHAT_RUN_VERSION
    trace_id: str
    created_at: str
    timestamp: str | None = None
    source: str = "chat"
    endpoint: str = CHAT_RUN_ENDPOINT
    input: str
    response: str | None = None
    model: str | None = None
    provider: str | None = None
    requested_model: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    top_p: float | None = None
    generation_config: dict[str, int | float] | None = None
    status: str
    retrieval_status: str | None = None
    chunk_ids: list[int] = Field(default_factory=list)
    document_ids: list[int] = Field(default_factory=list)
    source_filenames: list[str] = Field(default_factory=list)
    source_intent: str | None = None
    selected_corpus: str | None = None
    active_document_id: int | None = None
    active_document_title: str | None = None
    active_context_used: bool | None = None
    ranking_scores: list[int] = Field(default_factory=list)
    tokens_input: int | float | None = None
    tokens_output: int | float | None = None
    tokens_total: int | float | None = None
    prompt_eval_count: int | float | None = None
    eval_count: int | float | None = None
    prompt_eval_duration: int | float | None = None
    eval_duration: int | float | None = None
    total_duration: int | float | None = None
    load_duration: int | float | None = None
    output_tokens_per_second: int | float | None = None
    latency_ms: int | float | None = None
    generation_latency_ms: int | float | None = None
    retrieval_latency_ms: int | float | None = None
    tool_latency_ms: int | float | None = None
    error_code: str | None = None
    error_message: str | None = None
    warnings: list[str] = Field(default_factory=list)
    use_rag: bool | None = None
    evidence_used: bool | None = None
    fallback_used: bool | None = None
    fallback_reason: str | None = None
    answer_mode: str | None = None
    command: str | None = None
    tool_called: str | None = None
    tool_result_status: str | None = None
    document_path: str | None = None
    document_filename: str | None = None
    chars_written: int | None = None
    overwrite_requested: bool | None = None
    overwrite_applied: bool | None = None
    overwrite_reason: str | None = None
    error_type: str | None = None
    conversation_id: str | None = None
    conversation_window: int | None = None
    conversation_messages_used: int | None = None


def normalize_chat_run_record(record: dict[str, Any]) -> ChatRunRecord:
    created_at = _nullable_str(record.get("created_at")) or _utc_timestamp().isoformat()
    prompt_eval_count = _nullable_number(record.get("prompt_eval_count"))
    eval_count = _nullable_number(record.get("eval_count"))
    tokens_input = _nullable_number(record.get("tokens_input"))
    if tokens_input is None:
        tokens_input = prompt_eval_count
    tokens_output = _nullable_number(record.get("tokens_output"))
    if tokens_output is None:
        tokens_output = eval_count
    use_rag = record.get("use_rag") if isinstance(record.get("use_rag"), bool) else None
    temperature = _nullable_temperature(record.get("temperature"))
    if temperature is None and isinstance(record.get("generation_config"), dict):
        temperature = _nullable_temperature(record["generation_config"].get("temperature"))
    top_p = _nullable_top_p(record.get("top_p"))
    if top_p is None and isinstance(record.get("generation_config"), dict):
        top_p = _nullable_top_p(record["generation_config"].get("top_p"))
    max_tokens = _nullable_int(record.get("max_tokens"))
    if max_tokens is None and isinstance(record.get("generation_config"), dict):
        max_tokens = _nullable_int(record["generation_config"].get("max_tokens"))

    payload = {
        "version": _nullable_str(record.get("version")) or CHAT_RUN_VERSION,
        "trace_id": _nullable_str(record.get("trace_id")) or "",
        "created_at": created_at,
        "timestamp": _nullable_str(record.get("timestamp")) or created_at,
        "source": _normalize_source(record.get("source")),
        "endpoint": _normalize_endpoint(record.get("endpoint")),
        "input": _nullable_str(record.get("input")) or "",
        "response": _nullable_str(record.get("response")),
        "model": _nullable_str(record.get("model")),
        "provider": _nullable_str(record.get("provider")),
        "requested_model": _nullable_str(record.get("requested_model")),
        "temperature": temperature,
        "max_tokens": max_tokens,
        "top_p": top_p,
        "generation_config": _normalized_generation_config(record, temperature, top_p, max_tokens),
        "status": _nullable_str(record.get("status")) or "error",
        "retrieval_status": _normalize_retrieval_status(record.get("retrieval_status")),
        "chunk_ids": _int_list(record.get("chunk_ids")),
        "document_ids": _int_list(record.get("document_ids")),
        "source_filenames": _str_list(record.get("source_filenames")),
        "source_intent": _nullable_str(record.get("source_intent")),
        "selected_corpus": _nullable_str(record.get("selected_corpus")),
        "active_document_id": _nullable_int(record.get("active_document_id")),
        "active_document_title": _nullable_str(record.get("active_document_title")),
        "active_context_used": (
            record.get("active_context_used")
            if isinstance(record.get("active_context_used"), bool)
            else None
        ),
        "ranking_scores": _int_list(record.get("ranking_scores")),
        "tokens_input": tokens_input,
        "tokens_output": tokens_output,
        "tokens_total": _normalize_tokens_total(
            record=record,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
        ),
        "prompt_eval_count": prompt_eval_count if prompt_eval_count is not None else tokens_input,
        "eval_count": eval_count if eval_count is not None else tokens_output,
        "prompt_eval_duration": _nullable_number(record.get("prompt_eval_duration")),
        "eval_duration": _nullable_number(record.get("eval_duration")),
        "total_duration": _nullable_number(record.get("total_duration")),
        "load_duration": _nullable_number(record.get("load_duration")),
        "output_tokens_per_second": _normalize_output_tokens_per_second(
            record=record,
            tokens_output=tokens_output,
        ),
        "latency_ms": _nullable_number(record.get("latency_ms")),
        "generation_latency_ms": _nullable_number(record.get("generation_latency_ms")),
        "retrieval_latency_ms": _nullable_number(record.get("retrieval_latency_ms")),
        "tool_latency_ms": _nullable_number(record.get("tool_latency_ms")),
        "error_code": _nullable_str(record.get("error_code")),
        "error_message": _nullable_str(record.get("error_message")),
        "warnings": _warnings_list(record.get("warnings")),
        "use_rag": use_rag,
        "evidence_used": record.get("evidence_used") if isinstance(record.get("evidence_used"), bool) else None,
        "fallback_used": record.get("fallback_used") if isinstance(record.get("fallback_used"), bool) else None,
        "fallback_reason": _nullable_str(record.get("fallback_reason")),
        "answer_mode": _nullable_str(record.get("answer_mode")),
        "command": _nullable_str(record.get("command")),
        "tool_called": _nullable_str(record.get("tool_called")),
        "tool_result_status": _nullable_str(record.get("tool_result_status")),
        "document_path": _nullable_str(record.get("document_path")),
        "document_filename": _nullable_str(record.get("document_filename")),
        "chars_written": _nullable_int(record.get("chars_written")),
        "overwrite_requested": record.get("overwrite_requested") if isinstance(record.get("overwrite_requested"), bool) else None,
        "overwrite_applied": record.get("overwrite_applied") if isinstance(record.get("overwrite_applied"), bool) else None,
        "overwrite_reason": _nullable_str(record.get("overwrite_reason")),
        "error_type": _nullable_str(record.get("error_type")) or _nullable_str(record.get("error_code")),
        "conversation_id": _nullable_str(record.get("conversation_id")),
        "conversation_window": _nullable_int(record.get("conversation_window")),
        "conversation_messages_used": _nullable_int(record.get("conversation_messages_used")),
    }
    return ChatRunRecord(**payload)


def _safe_trace_id(value: str) -> str:
    candidate = re.sub(r"[^A-Za-z0-9_-]+", "_", value.strip())
    return candidate or "trace"


def _timestamp_for_filename(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        parsed = _utc_timestamp()
    return _utc_timestamp(parsed).strftime("%Y%m%dT%H%M%S%fZ")


def _run_filename(run: ChatRunRecord) -> str:
    return f"chat_run_{_timestamp_for_filename(run.created_at)}_{_safe_trace_id(run.trace_id)}{CHAT_RUN_FILE_SUFFIX}"


def record_chat_run(run: ChatRunRecord, *, path: Path | None = None) -> Path:
    output_path = resolve_chat_runs_path(path)
    output_path.mkdir(parents=True, exist_ok=True)
    payload = run.model_dump()
    run_path = output_path / _run_filename(run)
    run_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    return run_path


def _load_chat_run_file(path: Path) -> ChatRunRecord | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        log_event(
            component="frontend.chat.runs",
            event="chat_run_file_skipped",
            level=logging.WARNING,
            path=str(path),
            error_code="chat_run_json_invalid",
            error_message=str(exc),
        )
        return None

    if not isinstance(payload, dict):
        return None

    if payload.get("source") not in CHAT_RUN_SOURCES:
        return None

    try:
        return normalize_chat_run_record(payload)
    except Exception as exc:
        log_event(
            component="frontend.chat.runs",
            event="chat_run_record_skipped",
            level=logging.WARNING,
            path=str(path),
            error_code="chat_run_record_invalid",
            error_message=str(exc),
        )
        return None


def _load_chat_runs(*, limit: int | None, path: Path) -> list[ChatRunRecord]:
    if not path.exists() or not path.is_dir():
        return []

    records: list[ChatRunRecord] = []
    for run_path in sorted(path.glob(f"*{CHAT_RUN_FILE_SUFFIX}")):
        record = _load_chat_run_file(run_path)
        if record is not None:
            records.append(record)

    records.sort(key=lambda item: item.created_at, reverse=True)
    if limit is None:
        return records
    return records[:limit]


def list_chat_runs(limit: int | None = 50, *, path: Path | None = None) -> list[ChatRunRecord]:
    resolved_path = resolve_chat_runs_path(path)
    return _load_chat_runs(limit=limit, path=resolved_path)


def get_chat_run(trace_id: str, *, path: Path | None = None) -> ChatRunRecord | None:
    if not isinstance(trace_id, str) or not trace_id.strip():
        return None

    normalized_trace_id = trace_id.strip()
    for record in list_chat_runs(limit=None, path=path):
        if record.trace_id == normalized_trace_id:
            return record
    return None


def clear_chat_runs(*, path: Path | None = None) -> int:
    output_path = resolve_chat_runs_path(path)
    if not output_path.exists() or not output_path.is_dir():
        return 0

    removed_count = 0
    for run_path in output_path.glob(f"*{CHAT_RUN_FILE_SUFFIX}"):
        run_path.unlink()
        removed_count += 1
    return removed_count


def save_chat_run(run_payload: dict[str, Any], *, path: Path | None = None) -> Path:
    return record_chat_run(normalize_chat_run_record(run_payload), path=path)


def write_chat_run(**kwargs: Any) -> Path:
    created_at = _utc_timestamp(kwargs.get("created_at")).isoformat()
    prompt_eval_count = _nullable_number(kwargs.get("prompt_eval_count"))
    eval_count = _nullable_number(kwargs.get("eval_count"))
    tokens_input = _nullable_number(kwargs.get("tokens_input"))
    if tokens_input is None:
        tokens_input = prompt_eval_count
    tokens_output = _nullable_number(kwargs.get("tokens_output"))
    if tokens_output is None:
        tokens_output = eval_count
    run = ChatRunRecord(
        version=CHAT_RUN_VERSION,
        trace_id=kwargs["trace_id"],
        created_at=created_at,
        timestamp=created_at,
        source=_normalize_source(kwargs.get("source")),
        endpoint=_normalize_endpoint(kwargs.get("endpoint")),
        input=kwargs.get("input_text") or "",
        response=kwargs.get("response_text"),
        provider=kwargs.get("provider"),
        model=kwargs.get("model"),
        requested_model=kwargs.get("requested_model"),
        temperature=_nullable_temperature(kwargs.get("temperature")),
        max_tokens=_nullable_int(kwargs.get("max_tokens")),
        top_p=_nullable_top_p(kwargs.get("top_p")),
        generation_config=_normalized_generation_config(
            kwargs,
            _nullable_temperature(kwargs.get("temperature")),
            _nullable_top_p(kwargs.get("top_p")),
            _nullable_int(kwargs.get("max_tokens")),
        ),
        status=kwargs.get("status") or "error",
        retrieval_status=_normalize_retrieval_status(kwargs.get("retrieval_status")),
        chunk_ids=_int_list(kwargs.get("chunk_ids")),
        document_ids=_int_list(kwargs.get("document_ids")),
        source_filenames=_str_list(kwargs.get("source_filenames")),
        source_intent=_nullable_str(kwargs.get("source_intent")),
        selected_corpus=_nullable_str(kwargs.get("selected_corpus")),
        active_document_id=_nullable_int(kwargs.get("active_document_id")),
        active_document_title=_nullable_str(kwargs.get("active_document_title")),
        active_context_used=(
            kwargs.get("active_context_used")
            if isinstance(kwargs.get("active_context_used"), bool)
            else None
        ),
        ranking_scores=_int_list(kwargs.get("ranking_scores")),
        tokens_input=tokens_input,
        tokens_output=tokens_output,
        tokens_total=_normalize_tokens_total(
            record=kwargs,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
        ),
        prompt_eval_count=prompt_eval_count if prompt_eval_count is not None else tokens_input,
        eval_count=eval_count if eval_count is not None else tokens_output,
        prompt_eval_duration=_nullable_number(kwargs.get("prompt_eval_duration")),
        eval_duration=_nullable_number(kwargs.get("eval_duration")),
        total_duration=_nullable_number(kwargs.get("total_duration")),
        load_duration=_nullable_number(kwargs.get("load_duration")),
        output_tokens_per_second=_normalize_output_tokens_per_second(
            record=kwargs,
            tokens_output=tokens_output,
        ),
        latency_ms=_nullable_number(kwargs.get("latency_ms")),
        generation_latency_ms=_nullable_number(kwargs.get("generation_latency_ms")),
        retrieval_latency_ms=_nullable_number(kwargs.get("retrieval_latency_ms")),
        tool_latency_ms=_nullable_number(kwargs.get("tool_latency_ms")),
        error_code=_nullable_str(kwargs.get("error_code")),
        error_message=_nullable_str(kwargs.get("error_message")),
        warnings=_warnings_list(kwargs.get("warnings")),
        use_rag=kwargs.get("use_rag") if isinstance(kwargs.get("use_rag"), bool) else None,
        evidence_used=kwargs.get("evidence_used") if isinstance(kwargs.get("evidence_used"), bool) else None,
        fallback_used=kwargs.get("fallback_used") if isinstance(kwargs.get("fallback_used"), bool) else None,
        fallback_reason=_nullable_str(kwargs.get("fallback_reason")),
        answer_mode=_nullable_str(kwargs.get("answer_mode")),
        conversation_id=_nullable_str(kwargs.get("conversation_id")),
        conversation_window=_nullable_int(kwargs.get("conversation_window")),
        conversation_messages_used=_nullable_int(kwargs.get("conversation_messages_used")),
    )
    return record_chat_run(run, path=kwargs.get("path"))
