from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from app.config import settings
from app.evals.schemas import RunRecord
from app.observability.logging import log_event


REPO_ROOT = Path(__file__).resolve().parents[2]
NO_EVIDENCE_STATUSES = {"NO_EVIDENCE", "NO_EVIDENCE_FOR_ANSWER"}


@dataclass
class LoadedRuns:
    runs_dir: Path
    items: list[RunRecord] = field(default_factory=list)
    corrupt_files: list[str] = field(default_factory=list)
    skipped_files: list[str] = field(default_factory=list)


def _resolve_path(value: str) -> Path:
    candidate = Path(value.strip())
    if candidate.is_absolute():
        resolved = candidate
    else:
        resolved = REPO_ROOT / candidate
    if resolved.suffix.lower() in {".json", ".jsonl"}:
        return resolved.parent / resolved.stem
    return resolved


def resolve_runs_dir() -> Path:
    for env_name in ("CHAT_RUNS_DIR", "EVAL_RUNS_DIR"):
        raw_value = os.getenv(env_name)
        if isinstance(raw_value, str) and raw_value.strip():
            return _resolve_path(raw_value)

    configured = getattr(settings, "chat_runs_path", None)
    if isinstance(configured, str) and configured.strip():
        configured_path = _resolve_path(configured)
        if configured_path.exists():
            return configured_path

    chat_runs_dir = REPO_ROOT / "CHAT_RUNS"
    if chat_runs_dir.exists():
        return chat_runs_dir

    return REPO_ROOT / "evals" / "runs"


def _nullable_str(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    candidate = value.strip()
    return candidate or None


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


def _nullable_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _normalize_retrieval_status(value: Any) -> str | None:
    normalized = _nullable_str(value)
    if normalized in NO_EVIDENCE_STATUSES:
        return "NO_EVIDENCE"
    return normalized


def _tokens_total(payload: dict[str, Any], tokens_input: int | None, tokens_output: int | None) -> int | None:
    tokens_total = _nullable_int(payload.get("tokens_total"))
    if tokens_total is not None:
        return tokens_total
    if tokens_input is None or tokens_output is None:
        return None
    return tokens_input + tokens_output


def _output_tokens_per_second(payload: dict[str, Any], tokens_output: int | None) -> float | None:
    explicit_value = _nullable_float(payload.get("output_tokens_per_second"))
    if explicit_value is not None:
        return explicit_value

    eval_duration = _nullable_float(payload.get("eval_duration"))
    if tokens_output is None or eval_duration is None or eval_duration <= 0:
        return None

    return round(tokens_output / (eval_duration / 1_000_000_000), 4)


def _sort_key(run: RunRecord) -> tuple[int, str]:
    created_at = run.created_at
    if not isinstance(created_at, str):
        return (0, "")
    try:
        return (1, datetime.fromisoformat(created_at.replace("Z", "+00:00")).isoformat())
    except ValueError:
        return (0, created_at)


def _is_incompatible_run_payload(payload: dict[str, Any]) -> bool:
    version = _nullable_str(payload.get("version"))
    if version == "chat_eval_run.v1":
        return True
    return isinstance(payload.get("results"), list) and "summary" in payload and "run_id" in payload


def _normalize_run(payload: dict[str, Any], *, raw_filename: str) -> RunRecord:
    prompt_eval_count = _nullable_int(payload.get("prompt_eval_count"))
    eval_count = _nullable_int(payload.get("eval_count"))
    tokens_input = _nullable_int(payload.get("tokens_input"))
    if tokens_input is None:
        tokens_input = prompt_eval_count
    tokens_output = _nullable_int(payload.get("tokens_output"))
    if tokens_output is None:
        tokens_output = eval_count

    return RunRecord(
        trace_id=_nullable_str(payload.get("trace_id")),
        created_at=_nullable_str(payload.get("created_at")) or _nullable_str(payload.get("timestamp")),
        model=_nullable_str(payload.get("model")),
        latency_ms=_nullable_float(payload.get("latency_ms")),
        tokens_input=tokens_input,
        tokens_output=tokens_output,
        tokens_total=_tokens_total(payload, tokens_input, tokens_output),
        output_tokens_per_second=_output_tokens_per_second(payload, tokens_output),
        status=_nullable_str(payload.get("status")),
        error_code=_nullable_str(payload.get("error_code")) or _nullable_str(payload.get("code")),
        error_message=_nullable_str(payload.get("error_message")) or _nullable_str(payload.get("message")),
        retrieval_status=_normalize_retrieval_status(payload.get("retrieval_status")),
        fallback_used=payload.get("fallback_used") if isinstance(payload.get("fallback_used"), bool) else None,
        source=_nullable_str(payload.get("source")),
        raw_filename=raw_filename,
    )


def load_runs(*, runs_dir: Path | None = None, limit: int | None = None) -> LoadedRuns:
    resolved_dir = runs_dir or resolve_runs_dir()
    result = LoadedRuns(runs_dir=resolved_dir)

    if not resolved_dir.exists() or not resolved_dir.is_dir():
        return result

    for file_path in sorted(resolved_dir.glob("*.json")):
        try:
            payload = json.loads(file_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            result.corrupt_files.append(file_path.name)
            log_event(
                component="backend.runs.loader",
                event="run_file_corrupt",
                level=logging.WARNING,
                path=str(file_path),
                error_code="run_json_invalid",
                error_message=str(exc),
            )
            continue

        if not isinstance(payload, dict):
            result.corrupt_files.append(file_path.name)
            log_event(
                component="backend.runs.loader",
                event="run_file_corrupt",
                level=logging.WARNING,
                path=str(file_path),
                error_code="run_payload_not_object",
            )
            continue

        if _is_incompatible_run_payload(payload):
            result.skipped_files.append(file_path.name)
            continue

        try:
            result.items.append(_normalize_run(payload, raw_filename=file_path.name))
        except Exception as exc:
            result.corrupt_files.append(file_path.name)
            log_event(
                component="backend.runs.loader",
                event="run_file_corrupt",
                level=logging.WARNING,
                path=str(file_path),
                error_code="run_payload_invalid",
                error_message=str(exc),
            )

    result.items.sort(key=_sort_key, reverse=True)
    if isinstance(limit, int) and limit > 0:
        result.items = result.items[:limit]
    return result
