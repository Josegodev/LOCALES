import json
import logging
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.observability.logging import log_event


REPO_ROOT = Path(__file__).resolve().parents[2]
CHAT_EVAL_RUNS_DIR = REPO_ROOT / "evals" / "runs"
CHAT_TRACE_PREFIX = "chat_frontend_eval_"
CHAT_TRACE_SOURCES = {"frontend", "chat"}
UNKNOWN_MODEL_NAME = "unknown_model"
MAX_SAFE_MODEL_NAME_LENGTH = 80


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


def _warnings_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def safe_model_name(model: str | None) -> str:
    candidate = (model or "").strip() or UNKNOWN_MODEL_NAME
    normalized = re.sub(r"[^a-zA-Z0-9_.-]+", "_", candidate)
    normalized = normalized.strip("._-") or UNKNOWN_MODEL_NAME
    return normalized[:MAX_SAFE_MODEL_NAME_LENGTH]


def build_chat_eval_path(
    *,
    created_at: datetime | None = None,
    model: str | None = None,
    base_dir: Path | None = None,
) -> Path:
    timestamp = _utc_timestamp(created_at)
    resolved_base_dir = base_dir or CHAT_EVAL_RUNS_DIR
    return resolved_base_dir / (
        f"{CHAT_TRACE_PREFIX}{timestamp:%Y%m%dT%H%M%S%fZ}_{safe_model_name(model)}.json"
    )


def write_chat_eval_run(
    *,
    trace_id: str,
    source: str,
    input_text: str,
    response_text: str | None,
    provider: str | None,
    model: str | None,
    status: str,
    retrieval_status: str | None,
    chunk_ids: list[int] | None,
    latency_ms: int,
    error_code: str | None,
    error_message: str | None,
    warnings: list[str] | None,
    created_at: datetime | None = None,
    tokens_input: int | float | None = None,
    tokens_output: int | float | None = None,
    tokens_total: int | float | None = None,
    use_rag: bool | None = None,
    evidence_used: bool | None = None,
    fallback_used: bool | None = None,
    answer_mode: str | None = None,
    base_dir: Path | None = None,
) -> Path:
    timestamp = _utc_timestamp(created_at)
    resolved_base_dir = base_dir or CHAT_EVAL_RUNS_DIR
    resolved_base_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "trace_id": trace_id,
        "created_at": timestamp.isoformat(),
        "source": source if source in CHAT_TRACE_SOURCES else "chat",
        "input": input_text,
        "response": response_text,
        "provider": provider,
        "model": model,
        "status": status,
        "retrieval_status": retrieval_status,
        "chunk_ids": chunk_ids or [],
        "tokens_input": tokens_input,
        "tokens_output": tokens_output,
        "tokens_total": tokens_total,
        "latency_ms": latency_ms,
        "error_code": error_code,
        "error_message": error_message,
        "warnings": _warnings_list(warnings),
        "use_rag": use_rag,
        "evidence_used": evidence_used,
        "fallback_used": fallback_used,
        "answer_mode": answer_mode,
    }
    output_path = build_chat_eval_path(
        created_at=timestamp,
        model=model,
        base_dir=resolved_base_dir,
    )

    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=resolved_base_dir,
        prefix=f"{output_path.stem}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        json.dump(payload, handle, ensure_ascii=True, indent=2)
        handle.write("\n")
        temporary_path = Path(handle.name)

    os.replace(temporary_path, output_path)
    return output_path


def normalize_chat_eval_run(record: dict[str, Any]) -> dict[str, Any]:
    tokens_input = _nullable_number(record.get("tokens_input"))
    tokens_output = _nullable_number(record.get("tokens_output"))
    tokens_total = _nullable_number(record.get("tokens_total"))
    if tokens_total is None and tokens_input is not None and tokens_output is not None:
        tokens_total = tokens_input + tokens_output

    chunk_ids = record.get("chunk_ids")
    if not isinstance(chunk_ids, list):
        chunk_ids = []

    return {
        "trace_id": _nullable_str(record.get("trace_id")),
        "created_at": _nullable_str(record.get("created_at")),
        "source": _nullable_str(record.get("source")),
        "input": _nullable_str(record.get("input")),
        "response": _nullable_str(record.get("response")),
        "provider": _nullable_str(record.get("provider")),
        "model": _nullable_str(record.get("model")),
        "status": _nullable_str(record.get("status")),
        "retrieval_status": _nullable_str(record.get("retrieval_status")),
        "chunk_ids": [item for item in chunk_ids if isinstance(item, int)],
        "tokens_input": tokens_input,
        "tokens_output": tokens_output,
        "tokens_total": tokens_total,
        "latency_ms": _nullable_number(record.get("latency_ms")),
        "error_code": _nullable_str(record.get("error_code")),
        "error_message": _nullable_str(record.get("error_message")),
        "warnings": _warnings_list(record.get("warnings")),
        "use_rag": record.get("use_rag") if isinstance(record.get("use_rag"), bool) else None,
        "evidence_used": record.get("evidence_used") if isinstance(record.get("evidence_used"), bool) else None,
        "fallback_used": record.get("fallback_used") if isinstance(record.get("fallback_used"), bool) else None,
        "answer_mode": _nullable_str(record.get("answer_mode")),
    }


def _chat_eval_sort_key(record: dict[str, Any]) -> tuple[int, str]:
    created_at = record.get("created_at")
    if isinstance(created_at, str):
        return (1, created_at)
    return (0, "")


def load_chat_eval_runs(
    *,
    limit: int = 100,
    base_dir: Path | None = None,
) -> list[dict[str, Any]]:
    resolved_base_dir = base_dir or CHAT_EVAL_RUNS_DIR
    records: list[dict[str, Any]] = []

    for path in resolved_base_dir.glob(f"{CHAT_TRACE_PREFIX}*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            log_event(
                component="frontend.chat.evals",
                event="chat_eval_json_skipped",
                level=logging.WARNING,
                path=str(path),
                error_code="chat_eval_json_invalid",
                error_message=str(exc),
            )
            continue

        if not isinstance(payload, dict):
            log_event(
                component="frontend.chat.evals",
                event="chat_eval_json_skipped",
                level=logging.WARNING,
                path=str(path),
                error_code="chat_eval_json_invalid",
                error_message="chat eval JSON must be an object",
            )
            continue

        if payload.get("source") not in CHAT_TRACE_SOURCES:
            continue

        records.append(normalize_chat_eval_run(payload))

    records.sort(key=_chat_eval_sort_key, reverse=True)
    return records[:limit]
