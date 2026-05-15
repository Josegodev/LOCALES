import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from app.config import settings
from app.observability.logging import log_event


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CHAT_RUNS_PATH = REPO_ROOT / "data" / "chat_runs.jsonl"
CHAT_RUN_SOURCES = {"frontend", "chat"}
CHAT_RUN_ENDPOINT = "/chat"
CHAT_RUN_VERSION = "chat_run.v1"


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


def _runs_path(path: Path | None = None) -> Path:
    if path is not None:
        return path

    configured = getattr(settings, "chat_runs_path", None)
    if isinstance(configured, str) and configured.strip():
        candidate = Path(configured.strip())
        if not candidate.is_absolute():
            candidate = REPO_ROOT / candidate
        return candidate

    return DEFAULT_CHAT_RUNS_PATH


class ChatRunRecord(BaseModel):
    version: str = CHAT_RUN_VERSION
    trace_id: str
    created_at: str
    source: str = "frontend"
    endpoint: str = CHAT_RUN_ENDPOINT
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


def normalize_chat_run_record(record: dict[str, Any]) -> ChatRunRecord:
    tokens_input = _nullable_number(record.get("tokens_input"))
    tokens_output = _nullable_number(record.get("tokens_output"))
    use_rag = record.get("use_rag") if isinstance(record.get("use_rag"), bool) else None

    payload = {
        "version": _nullable_str(record.get("version")) or CHAT_RUN_VERSION,
        "trace_id": _nullable_str(record.get("trace_id")) or "",
        "created_at": _nullable_str(record.get("created_at")) or _utc_timestamp().isoformat(),
        "source": _normalize_source(record.get("source")),
        "endpoint": _normalize_endpoint(record.get("endpoint")),
        "input": _nullable_str(record.get("input")) or "",
        "response": _nullable_str(record.get("response")),
        "model": _nullable_str(record.get("model")),
        "provider": _nullable_str(record.get("provider")),
        "status": _nullable_str(record.get("status")) or "error",
        "retrieval_status": _normalize_retrieval_status(record.get("retrieval_status")),
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
    return ChatRunRecord(**payload)


def record_chat_run(run: ChatRunRecord, *, path: Path | None = None) -> None:
    output_path = _runs_path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = run.model_dump()

    with output_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=True))
        handle.write("\n")


def _load_jsonl_chat_runs(*, limit: int, path: Path) -> list[ChatRunRecord]:
    if not path.exists():
        return []

    records: list[ChatRunRecord] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            log_event(
                component="frontend.chat.runs",
                event="chat_run_jsonl_skipped",
                level=logging.WARNING,
                path=str(path),
                line_number=line_number,
                error_code="chat_run_json_invalid",
                error_message=str(exc),
            )
            continue

        if not isinstance(payload, dict):
            continue

        if payload.get("source") not in CHAT_RUN_SOURCES:
            continue

        try:
            record = normalize_chat_run_record(payload)
        except Exception as exc:
            log_event(
                component="frontend.chat.runs",
                event="chat_run_record_skipped",
                level=logging.WARNING,
                path=str(path),
                line_number=line_number,
                error_code="chat_run_record_invalid",
                error_message=str(exc),
            )
            continue
        records.append(record)

    records.sort(key=lambda item: item.created_at, reverse=True)
    return records[:limit]


def list_chat_runs(limit: int = 50, *, path: Path | None = None) -> list[ChatRunRecord]:
    resolved_path = _runs_path(path)
    return _load_jsonl_chat_runs(limit=limit, path=resolved_path)


def clear_chat_runs(*, path: Path | None = None) -> int:
    output_path = _runs_path(path)
    if not output_path.exists():
        return 0

    removed_count = sum(
        1 for line in output_path.read_text(encoding="utf-8").splitlines() if line.strip()
    )
    output_path.write_text("", encoding="utf-8")
    return removed_count


def write_chat_run(**kwargs: Any) -> None:
    run = ChatRunRecord(
        version=CHAT_RUN_VERSION,
        trace_id=kwargs["trace_id"],
        created_at=_utc_timestamp(kwargs.get("created_at")).isoformat(),
        source=_normalize_source(kwargs.get("source")),
        endpoint=_normalize_endpoint(kwargs.get("endpoint")),
        input=kwargs.get("input_text") or "",
        response=kwargs.get("response_text"),
        provider=kwargs.get("provider"),
        model=kwargs.get("model"),
        status=kwargs.get("status") or "error",
        retrieval_status=_normalize_retrieval_status(kwargs.get("retrieval_status")),
        chunk_ids=_int_list(kwargs.get("chunk_ids")),
        document_ids=_int_list(kwargs.get("document_ids")),
        source_filenames=_str_list(kwargs.get("source_filenames")),
        tokens_input=_nullable_number(kwargs.get("tokens_input")),
        tokens_output=_nullable_number(kwargs.get("tokens_output")),
        tokens_total=_normalize_tokens_total(
            record=kwargs,
            tokens_input=_nullable_number(kwargs.get("tokens_input")),
            tokens_output=_nullable_number(kwargs.get("tokens_output")),
        ),
        latency_ms=_nullable_number(kwargs.get("latency_ms")),
        error_code=_nullable_str(kwargs.get("error_code")),
        error_message=_nullable_str(kwargs.get("error_message")),
        warnings=_warnings_list(kwargs.get("warnings")),
        use_rag=kwargs.get("use_rag") if isinstance(kwargs.get("use_rag"), bool) else None,
        evidence_used=kwargs.get("evidence_used") if isinstance(kwargs.get("evidence_used"), bool) else None,
        fallback_used=kwargs.get("fallback_used") if isinstance(kwargs.get("fallback_used"), bool) else None,
        answer_mode=_nullable_str(kwargs.get("answer_mode")),
    )
    record_chat_run(run, path=kwargs.get("path"))
