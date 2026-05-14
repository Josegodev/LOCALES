import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from app.config import settings
from app.observability.logging import log_event


REPO_ROOT = Path(__file__).resolve().parents[2]
LEGACY_CHAT_EVAL_RUNS_DIR = REPO_ROOT / "evals" / "runs"
CHAT_EVAL_RUNS_DIR = LEGACY_CHAT_EVAL_RUNS_DIR
DEFAULT_CHAT_TRACE_PATH = REPO_ROOT / "data" / "chat_traces.jsonl"
CHAT_TRACE_SOURCES = {"frontend", "chat"}
CHAT_TRACE_ENDPOINT = "/chat"
LEGACY_CHAT_TRACE_PREFIX = "chat_frontend_eval_"


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
    if isinstance(value, str) and value in CHAT_TRACE_SOURCES:
        return value
    return "chat"


def _normalize_endpoint(value: Any) -> str:
    if isinstance(value, str) and value.strip():
        return value
    return CHAT_TRACE_ENDPOINT


def _normalize_retrieval_status(value: Any, *, use_rag: bool | None) -> str | None:
    if use_rag is False:
        return None
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    if not normalized or normalized in {"unknown", "DISABLED"}:
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


def _trace_path(path: Path | None = None) -> Path:
    if path is not None:
        return path

    configured = getattr(settings, "chat_trace_path", None)
    if isinstance(configured, str) and configured.strip():
        candidate = Path(configured.strip())
        if not candidate.is_absolute():
            candidate = REPO_ROOT / candidate
        return candidate

    return DEFAULT_CHAT_TRACE_PATH


class ChatTraceRecord(BaseModel):
    trace_id: str
    created_at: str
    source: str = "frontend"
    endpoint: str = CHAT_TRACE_ENDPOINT
    input: str
    response: str | None = None
    model: str | None = None
    provider: str | None = None
    status: str
    retrieval_status: str | None = None
    chunk_ids: list[int] = Field(default_factory=list)
    document_ids: list[int] = Field(default_factory=list)
    source_filenames: list[str] = Field(default_factory=list)
    tokens_input: int | float | None = None
    tokens_output: int | float | None = None
    tokens_total: int | float | None = None
    latency_ms: int | float | None = None
    error_code: str | None = None
    error_message: str | None = None
    warnings: list[str] = Field(default_factory=list)
    use_rag: bool | None = None
    evidence_used: bool | None = None
    fallback_used: bool | None = None
    answer_mode: str | None = None


def normalize_chat_trace_record(record: dict[str, Any]) -> ChatTraceRecord:
    tokens_input = _nullable_number(record.get("tokens_input"))
    tokens_output = _nullable_number(record.get("tokens_output"))
    use_rag = record.get("use_rag") if isinstance(record.get("use_rag"), bool) else None

    payload = {
        "trace_id": _nullable_str(record.get("trace_id")) or "",
        "created_at": _nullable_str(record.get("created_at")) or _utc_timestamp().isoformat(),
        "source": _normalize_source(record.get("source")),
        "endpoint": _normalize_endpoint(record.get("endpoint")),
        "input": _nullable_str(record.get("input")) or "",
        "response": _nullable_str(record.get("response")),
        "model": _nullable_str(record.get("model")),
        "provider": _nullable_str(record.get("provider")),
        "status": _nullable_str(record.get("status")) or "error",
        "retrieval_status": _normalize_retrieval_status(record.get("retrieval_status"), use_rag=use_rag),
        "chunk_ids": _int_list(record.get("chunk_ids")),
        "document_ids": _int_list(record.get("document_ids")),
        "source_filenames": _str_list(record.get("source_filenames")),
        "tokens_input": tokens_input,
        "tokens_output": tokens_output,
        "tokens_total": _normalize_tokens_total(
            record=record,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
        ),
        "latency_ms": _nullable_number(record.get("latency_ms")),
        "error_code": _nullable_str(record.get("error_code")),
        "error_message": _nullable_str(record.get("error_message")),
        "warnings": _warnings_list(record.get("warnings")),
        "use_rag": use_rag,
        "evidence_used": record.get("evidence_used") if isinstance(record.get("evidence_used"), bool) else None,
        "fallback_used": record.get("fallback_used") if isinstance(record.get("fallback_used"), bool) else None,
        "answer_mode": _nullable_str(record.get("answer_mode")),
    }
    return ChatTraceRecord(**payload)


def record_chat_trace(trace: ChatTraceRecord, *, path: Path | None = None) -> None:
    output_path = _trace_path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = trace.model_dump()

    with output_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=True))
        handle.write("\n")


def _load_jsonl_chat_traces(*, limit: int, path: Path) -> list[ChatTraceRecord]:
    if not path.exists():
        return []

    records: list[ChatTraceRecord] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            log_event(
                component="frontend.chat.traces",
                event="chat_trace_jsonl_skipped",
                level=logging.WARNING,
                path=str(path),
                line_number=line_number,
                error_code="chat_trace_json_invalid",
                error_message=str(exc),
            )
            continue

        if not isinstance(payload, dict):
            continue

        if payload.get("source") not in CHAT_TRACE_SOURCES:
            continue

        try:
            record = normalize_chat_trace_record(payload)
        except Exception as exc:
            log_event(
                component="frontend.chat.traces",
                event="chat_trace_record_skipped",
                level=logging.WARNING,
                path=str(path),
                line_number=line_number,
                error_code="chat_trace_record_invalid",
                error_message=str(exc),
            )
            continue
        records.append(record)

    records.sort(key=lambda item: item.created_at, reverse=True)
    return records[:limit]


def _load_legacy_chat_eval_runs(*, limit: int, base_dir: Path | None = None) -> list[ChatTraceRecord]:
    resolved_base_dir = base_dir or CHAT_EVAL_RUNS_DIR
    records: list[ChatTraceRecord] = []

    for path in resolved_base_dir.glob(f"{LEGACY_CHAT_TRACE_PREFIX}*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            log_event(
                component="frontend.chat.traces",
                event="legacy_chat_trace_skipped",
                level=logging.WARNING,
                path=str(path),
                error_code="chat_trace_json_invalid",
                error_message=str(exc),
            )
            continue

        if not isinstance(payload, dict):
            continue

        if payload.get("source") not in CHAT_TRACE_SOURCES:
            continue

        try:
            records.append(normalize_chat_trace_record(payload))
        except Exception as exc:
            log_event(
                component="frontend.chat.traces",
                event="legacy_chat_trace_skipped",
                level=logging.WARNING,
                path=str(path),
                error_code="chat_trace_record_invalid",
                error_message=str(exc),
            )

    records.sort(key=lambda item: item.created_at, reverse=True)
    return records[:limit]


def list_chat_traces(limit: int = 50, *, path: Path | None = None) -> list[ChatTraceRecord]:
    resolved_path = _trace_path(path)
    records = _load_jsonl_chat_traces(limit=limit, path=resolved_path)
    if records:
        return records[:limit]
    return _load_legacy_chat_eval_runs(limit=limit)


def write_chat_eval_run(**kwargs: Any) -> None:
    record = ChatTraceRecord(
        trace_id=kwargs["trace_id"],
        created_at=_utc_timestamp(kwargs.get("created_at")).isoformat(),
        source=_normalize_source(kwargs.get("source")),
        endpoint=_normalize_endpoint(kwargs.get("endpoint")),
        input=kwargs.get("input_text") or "",
        response=kwargs.get("response_text"),
        provider=kwargs.get("provider"),
        model=kwargs.get("model"),
        status=kwargs.get("status") or "error",
        retrieval_status=_normalize_retrieval_status(
            kwargs.get("retrieval_status"),
            use_rag=kwargs.get("use_rag") if isinstance(kwargs.get("use_rag"), bool) else None,
        ),
        chunk_ids=_int_list(kwargs.get("chunk_ids")),
        document_ids=_int_list(kwargs.get("document_ids")),
        source_filenames=_str_list(kwargs.get("source_filenames")),
        tokens_input=_nullable_number(kwargs.get("tokens_input")),
        tokens_output=_nullable_number(kwargs.get("tokens_output")),
        tokens_total=_nullable_number(kwargs.get("tokens_total")),
        latency_ms=_nullable_number(kwargs.get("latency_ms")),
        error_code=_nullable_str(kwargs.get("error_code")),
        error_message=_nullable_str(kwargs.get("error_message")),
        warnings=_warnings_list(kwargs.get("warnings")),
        use_rag=kwargs.get("use_rag") if isinstance(kwargs.get("use_rag"), bool) else None,
        evidence_used=kwargs.get("evidence_used") if isinstance(kwargs.get("evidence_used"), bool) else None,
        fallback_used=kwargs.get("fallback_used") if isinstance(kwargs.get("fallback_used"), bool) else None,
        answer_mode=_nullable_str(kwargs.get("answer_mode")),
    )
    record_chat_trace(record, path=kwargs.get("path"))


def load_chat_eval_runs(*, limit: int = 100, base_dir: Path | None = None) -> list[dict[str, Any]]:
    path = base_dir if isinstance(base_dir, Path) and base_dir.suffix == ".jsonl" else None
    return [record.model_dump() for record in list_chat_traces(limit=limit, path=path)]


def build_chat_eval_path(*args: Any, **kwargs: Any) -> Path:
    return _trace_path(kwargs.get("path"))
