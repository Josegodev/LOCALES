from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from math import isfinite
from pathlib import Path
from typing import Any

from app.observability.chat_runs import resolve_chat_runs_path
from app.observability.logging import log_event
from app.schemas import normalize_temperature


PROVIDER_NATIVE_METRIC_FIELDS = (
    "prompt_eval_duration",
    "eval_duration",
    "total_duration",
    "load_duration",
)


@dataclass
class LoadedChatRuns:
    runs_dir: Path
    items: list[dict[str, Any]] = field(default_factory=list)
    skipped_files: list[str] = field(default_factory=list)

    @property
    def skipped_files_count(self) -> int:
        return len(self.skipped_files)


def resolve_runs_dir() -> Path:
    return resolve_chat_runs_path()


def _nullable_str(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    candidate = value.strip()
    return candidate or None


def _nullable_bool(value: Any) -> bool | None:
    return value if isinstance(value, bool) else None


def _safe_number(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        number = float(value)
    elif isinstance(value, str):
        candidate = value.strip()
        if not candidate:
            return None
        try:
            number = float(candidate)
        except ValueError:
            return None
    else:
        return None

    if not isfinite(number):
        return None
    return number


def _nullable_temperature(payload: dict[str, Any]) -> float | None:
    direct_value = payload.get("temperature")
    if direct_value is not None:
        try:
            return normalize_temperature(direct_value)
        except (TypeError, ValueError):
            return None

    generation_config = payload.get("generation_config")
    if not isinstance(generation_config, dict):
        return None

    configured_temperature = generation_config.get("temperature")
    if configured_temperature is None:
        return None

    try:
        return normalize_temperature(configured_temperature)
    except (TypeError, ValueError):
        return None


def _int_list(value: Any) -> list[int]:
    if not isinstance(value, list):
        return []

    items: list[int] = []
    for item in value:
        if isinstance(item, bool):
            continue
        if isinstance(item, int):
            items.append(item)
            continue
        if isinstance(item, float) and item.is_integer():
            items.append(int(item))
            continue
        if isinstance(item, str) and item.strip().isdigit():
            items.append(int(item.strip()))
    return items


def _str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _normalized_tokens_total(payload: dict[str, Any], *, tokens_input: float | None, tokens_output: float | None) -> float | None:
    explicit_total = _safe_number(payload.get("tokens_total"))
    if explicit_total is not None:
        return explicit_total
    if tokens_input is None or tokens_output is None:
        return None
    return tokens_input + tokens_output


def _normalized_output_tokens_per_second(payload: dict[str, Any], *, tokens_output: float | None) -> float | None:
    explicit_value = _safe_number(payload.get("output_tokens_per_second"))
    if explicit_value is not None:
        return round(explicit_value, 4)

    eval_duration = _safe_number(payload.get("eval_duration"))
    if tokens_output is None or eval_duration is None or eval_duration <= 0:
        return None

    return round(tokens_output / (eval_duration / 1_000_000_000), 4)


def _normalized_retrieval_status(value: Any) -> str | None:
    normalized = _nullable_str(value)
    if normalized == "unknown":
        return None
    return normalized


def _infer_observability_level(payload: dict[str, Any]) -> str | None:
    explicit_level = _nullable_str(payload.get("observability_level"))
    if explicit_level is not None:
        return explicit_level

    if any(_safe_number(payload.get(field_name)) is not None for field_name in PROVIDER_NATIVE_METRIC_FIELDS):
        return "provider_native"

    if any(
        _safe_number(payload.get(field_name)) is not None
        for field_name in ("latency_ms", "generation_latency_ms", "retrieval_latency_ms")
    ):
        return "runtime_only"

    return None


def _is_incompatible_payload(payload: dict[str, Any]) -> bool:
    version = _nullable_str(payload.get("version"))
    if version == "chat_eval_run.v1":
        return True
    return isinstance(payload.get("results"), list) and "summary" in payload and "run_id" in payload


def normalize_run(payload: dict[str, Any]) -> dict[str, Any]:
    prompt_eval_count = _safe_number(payload.get("prompt_eval_count"))
    eval_count = _safe_number(payload.get("eval_count"))

    tokens_input = _safe_number(payload.get("tokens_input"))
    if tokens_input is None:
        tokens_input = prompt_eval_count

    tokens_output = _safe_number(payload.get("tokens_output"))
    if tokens_output is None:
        tokens_output = eval_count

    normalized = {
        "trace_id": _nullable_str(payload.get("trace_id")),
        "created_at": _nullable_str(payload.get("created_at")) or _nullable_str(payload.get("timestamp")),
        "source": _nullable_str(payload.get("source")) or "chat",
        "provider": _nullable_str(payload.get("provider")),
        "model": _nullable_str(payload.get("model")),
        "temperature": _nullable_temperature(payload),
        "use_rag": _nullable_bool(payload.get("use_rag")),
        "retrieval_status": _normalized_retrieval_status(payload.get("retrieval_status")),
        "status": _nullable_str(payload.get("status")) or "error",
        "fallback_used": _nullable_bool(payload.get("fallback_used")),
        "fallback_reason": _nullable_str(payload.get("fallback_reason")),
        "latency_ms": _safe_number(payload.get("latency_ms")),
        "retrieval_latency_ms": _safe_number(payload.get("retrieval_latency_ms")),
        "generation_latency_ms": _safe_number(payload.get("generation_latency_ms")),
        "tokens_input": tokens_input,
        "tokens_output": tokens_output,
        "tokens_total": _normalized_tokens_total(
            payload,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
        ),
        "output_tokens_per_second": _normalized_output_tokens_per_second(
            payload,
            tokens_output=tokens_output,
        ),
        "prompt_eval_duration": _safe_number(payload.get("prompt_eval_duration")),
        "eval_duration": _safe_number(payload.get("eval_duration")),
        "total_duration": _safe_number(payload.get("total_duration")),
        "load_duration": _safe_number(payload.get("load_duration")),
        "chunk_ids": _int_list(payload.get("chunk_ids")),
        "source_filenames": _str_list(payload.get("source_filenames")),
        "error_code": _nullable_str(payload.get("error_code")) or _nullable_str(payload.get("code")),
        "error_message": _nullable_str(payload.get("error_message")) or _nullable_str(payload.get("message")),
        "observability_level": _infer_observability_level(payload),
    }
    return normalized


def _sort_key(run: dict[str, Any]) -> tuple[int, str, str]:
    created_at = _nullable_str(run.get("created_at"))
    trace_id = _nullable_str(run.get("trace_id")) or ""
    if created_at is None:
        return (0, "", trace_id)

    try:
        parsed = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    except ValueError:
        return (0, created_at, trace_id)

    return (1, parsed.isoformat(), trace_id)


def load_chat_runs(*, runs_dir: Path | None = None, limit: int | None = None) -> LoadedChatRuns:
    resolved_dir = runs_dir or resolve_runs_dir()
    result = LoadedChatRuns(runs_dir=resolved_dir)

    if not resolved_dir.exists() or not resolved_dir.is_dir():
        return result

    for file_path in sorted(resolved_dir.glob("*.json")):
        try:
            payload = json.loads(file_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            result.skipped_files.append(file_path.name)
            log_event(
                component="backend.chat_runs.store",
                event="chat_run_file_skipped",
                level=logging.WARNING,
                path=str(file_path),
                error_code="chat_run_json_invalid",
                error_message=str(exc),
            )
            continue

        if not isinstance(payload, dict):
            result.skipped_files.append(file_path.name)
            log_event(
                component="backend.chat_runs.store",
                event="chat_run_file_skipped",
                level=logging.WARNING,
                path=str(file_path),
                error_code="chat_run_payload_not_object",
            )
            continue

        if _is_incompatible_payload(payload):
            result.skipped_files.append(file_path.name)
            continue

        try:
            result.items.append(normalize_run(payload))
        except Exception as exc:
            result.skipped_files.append(file_path.name)
            log_event(
                component="backend.chat_runs.store",
                event="chat_run_file_skipped",
                level=logging.WARNING,
                path=str(file_path),
                error_code="chat_run_payload_invalid",
                error_message=str(exc),
            )

    result.items.sort(key=_sort_key, reverse=True)
    if isinstance(limit, int) and limit > 0:
        result.items = result.items[:limit]
    return result


def get_chat_run(trace_id: str, *, runs_dir: Path | None = None) -> dict[str, Any] | None:
    candidate = trace_id.strip()
    if not candidate:
        return None

    loaded = load_chat_runs(runs_dir=runs_dir)
    for run in loaded.items:
        if run.get("trace_id") == candidate:
            return run
    return None
