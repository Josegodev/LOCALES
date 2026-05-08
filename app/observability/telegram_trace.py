import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
TELEGRAM_RUNS_DIR = REPO_ROOT / "logs" / "telegram_runs"
TELEGRAM_TRACE_OPTIONAL_FIELDS = (
    "provider",
    "temperature",
    "temperature_ignored",
    "tokens_input",
    "tokens_output",
    "tokens_total",
    "prompt_eval_count",
    "eval_count",
    "prompt_eval_duration_ns",
    "eval_duration_ns",
    "total_duration_ns",
    "load_duration_ns",
    "prompt_tokens_per_second",
    "output_tokens_per_second",
    "retrieval_status",
    "chunk_ids",
)


def telegram_trace_file_path(
    *,
    created_at: datetime | None = None,
    base_dir: Path | None = None,
) -> Path:
    timestamp = created_at or datetime.now(timezone.utc)
    resolved_base_dir = base_dir or TELEGRAM_RUNS_DIR
    return resolved_base_dir / f"telegram_chat_{timestamp:%Y%m%d}.jsonl"


def append_telegram_trace(
    *,
    trace_id: str,
    request_id: str,
    chat_id: int | None,
    user_id: int | None,
    command: str,
    text_chars: int,
    response_chars: int,
    model: str | None,
    status: str,
    error_code: str | None,
    latency_ms: int,
    created_at: datetime | None = None,
    include_text: bool = False,
    text: str | None = None,
    metadata: dict[str, Any] | None = None,
    base_dir: Path | None = None,
) -> Path:
    timestamp = created_at or datetime.now(timezone.utc)
    resolved_base_dir = base_dir or TELEGRAM_RUNS_DIR
    payload: dict[str, Any] = {
        "trace_id": trace_id,
        "request_id": request_id,
        "chat_id": chat_id,
        "user_id": user_id,
        "command": command,
        "text_chars": text_chars,
        "response_chars": response_chars,
        "model": model,
        "status": status,
        "error_code": error_code,
        "latency_ms": latency_ms,
        "created_at": timestamp.isoformat(),
    }

    if metadata:
        for field_name in TELEGRAM_TRACE_OPTIONAL_FIELDS:
            if field_name in metadata:
                payload[field_name] = metadata[field_name]

    if include_text and text is not None:
        payload["text"] = text

    resolved_base_dir.mkdir(parents=True, exist_ok=True)
    output_path = telegram_trace_file_path(created_at=timestamp, base_dir=resolved_base_dir)
    with output_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return output_path
