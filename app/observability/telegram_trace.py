import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
TELEGRAM_RUNS_DIR = REPO_ROOT / "logs" / "telegram_runs"
TELEGRAM_EVAL_RUNS_DIR = REPO_ROOT / "evals" / "runs"
TELEGRAM_CONVERSATION_RUNS_DIR = REPO_ROOT / "DB" / "conversations" / "telegram" / "runs"
TELEGRAM_PROMPT_VERSION = "telegram_rag_v1"
UNKNOWN_MODEL_NAME = "unknown_model"
MAX_SAFE_MODEL_NAME_LENGTH = 80
TELEGRAM_TRACE_OPTIONAL_FIELDS = (
    "provider",
    "temperature",
    "temperature_ignored",
    "generation_config",
    "prompt_version",
    "repo_tool",
    "repo_path",
    "question",
    "evidence_files",
    "requested_file",
    "resolved_path",
    "start_line",
    "end_line",
    "query",
    "query_original",
    "query_normalized",
    "query_terms",
    "quoted_terms",
    "source_intent",
    "selected_corpus",
    "active_document_id",
    "active_document_title",
    "active_context_used",
    "active_context_reason",
    "evidence_used",
    "fallback_used",
    "query_expansion_used",
    "query_expansion_reason",
    "expanded_query_terms",
    "candidate_filenames",
    "selected_filenames",
    "scores",
    "answer_mode",
    "final_message_preview",
    "top_k",
    "source_filenames",
    "use_rag",
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
    "document_ids",
    "warnings",
)


def _utc_timestamp(created_at: datetime | None = None) -> datetime:
    timestamp = created_at or datetime.now(timezone.utc)
    if timestamp.tzinfo is None:
        return timestamp.replace(tzinfo=timezone.utc)
    return timestamp.astimezone(timezone.utc)


def _build_telegram_trace_payload(
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
    response_text: str | None = None,
    error_message: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    timestamp = _utc_timestamp(created_at)
    source_filenames = metadata.get("source_filenames") if isinstance(metadata, dict) else None
    if not isinstance(source_filenames, list) or not all(isinstance(item, str) for item in source_filenames):
        source_filenames = []
    chunk_ids = metadata.get("chunk_ids") if isinstance(metadata, dict) else None
    if not isinstance(chunk_ids, list) or not all(isinstance(item, int) for item in chunk_ids):
        chunk_ids = []
    document_ids = metadata.get("document_ids") if isinstance(metadata, dict) else None
    if not isinstance(document_ids, list) or not all(isinstance(item, int) for item in document_ids):
        document_ids = []
    warnings = metadata.get("warnings") if isinstance(metadata, dict) else None
    warnings = _warnings_list(warnings)
    payload: dict[str, Any] = {
        "trace_id": trace_id,
        "request_id": request_id,
        "chat_id": chat_id,
        "user_id": user_id,
        "source": "telegram",
        "input": text,
        "response": response_text,
        "answer_length": len(response_text) if isinstance(response_text, str) else 0,
        "command": command,
        "text_chars": text_chars,
        "response_chars": response_chars,
        "model": model,
        "temperature": metadata.get("temperature") if isinstance(metadata, dict) else None,
        "generation_config": metadata.get("generation_config") if isinstance(metadata, dict) else None,
        "prompt_version": TELEGRAM_PROMPT_VERSION,
        "top_k": metadata.get("top_k") if isinstance(metadata, dict) else None,
        "source_filenames": source_filenames,
        "status": status,
        "error_code": error_code,
        "error_message": error_message,
        "retrieval_status": metadata.get("retrieval_status") if isinstance(metadata, dict) else None,
        "chunk_ids": chunk_ids,
        "document_ids": document_ids,
        "latency_ms": latency_ms,
        "warnings": warnings,
        "created_at": timestamp.isoformat(),
    }

    if metadata:
        for field_name in TELEGRAM_TRACE_OPTIONAL_FIELDS:
            if field_name in metadata:
                payload[field_name] = metadata[field_name]

    if include_text and text is not None:
        payload["text"] = text

    return payload


def _warnings_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _ollama_metrics_payload(payload: dict[str, Any]) -> dict[str, int] | None:
    keys = (
        "load_duration_ns",
        "prompt_eval_duration_ns",
        "eval_duration_ns",
        "total_duration_ns",
        "prompt_eval_count",
        "eval_count",
    )
    metrics = {
        key: payload[key]
        for key in keys
        if isinstance(payload.get(key), int)
    }
    return metrics or None


def _finalize_telegram_trace_payload(payload: dict[str, Any]) -> dict[str, Any]:
    output = dict(payload)
    ollama_metrics = _ollama_metrics_payload(output)
    if ollama_metrics is not None:
        output["ollama"] = ollama_metrics
    return output


def preserve_full_trace_record(record: dict[str, Any]) -> dict[str, Any]:
    return dict(record)


def build_eval_record_from_trace(record: dict[str, Any]) -> dict[str, Any]:
    output = preserve_full_trace_record(record)

    legacy_aliases = {
        "prompt_eval_duration": "prompt_eval_duration_ns",
        "eval_duration": "eval_duration_ns",
        "total_duration": "total_duration_ns",
        "load_duration": "load_duration_ns",
    }
    for target_key, source_key in legacy_aliases.items():
        if target_key not in output and source_key in output:
            output[target_key] = output[source_key]

    return output


def safe_model_name(model: str | None) -> str:
    if not isinstance(model, str):
        return UNKNOWN_MODEL_NAME

    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", model.strip())
    cleaned = cleaned[:MAX_SAFE_MODEL_NAME_LENGTH].strip("._-")
    return cleaned or UNKNOWN_MODEL_NAME


def telegram_trace_file_path(
    *,
    created_at: datetime | None = None,
    base_dir: Path | None = None,
) -> Path:
    timestamp = _utc_timestamp(created_at)
    resolved_base_dir = base_dir or TELEGRAM_RUNS_DIR
    return resolved_base_dir / f"telegram_chat_{timestamp:%Y%m%d}.jsonl"


def build_telegram_eval_path(
    *,
    created_at: datetime | None = None,
    model: str | None = None,
    base_dir: Path | None = None,
) -> Path:
    timestamp = _utc_timestamp(created_at)
    resolved_base_dir = base_dir or TELEGRAM_EVAL_RUNS_DIR
    return resolved_base_dir / f"chat_eval_{timestamp:%Y%m%dT%H%M%S%fZ}_{safe_model_name(model)}.json"


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
    response_text: str | None = None,
    error_message: str | None = None,
    metadata: dict[str, Any] | None = None,
    base_dir: Path | None = None,
) -> Path:
    timestamp = _utc_timestamp(created_at)
    resolved_base_dir = base_dir or TELEGRAM_RUNS_DIR
    payload = _build_telegram_trace_payload(
        trace_id=trace_id,
        request_id=request_id,
        chat_id=chat_id,
        user_id=user_id,
        command=command,
        text_chars=text_chars,
        response_chars=response_chars,
        model=model,
        status=status,
        error_code=error_code,
        latency_ms=latency_ms,
        created_at=timestamp,
        include_text=include_text,
        text=text,
        response_text=response_text,
        error_message=error_message,
        metadata=metadata,
    )
    # TODO(hardening): retirar los campos legacy planos de Ollama cuando los lectores
    # consuman de forma estable el bloque payload["ollama"].
    payload = _finalize_telegram_trace_payload(payload)
    resolved_base_dir.mkdir(parents=True, exist_ok=True)
    output_path = telegram_trace_file_path(created_at=timestamp, base_dir=resolved_base_dir)
    with output_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return output_path


def write_telegram_eval_run(
    *,
    trace_id: str,
    request_id: str | None = None,
    chat_id: int | None = None,
    user_id: int | None = None,
    command: str = "chat",
    model: str | None,
    input_text: str,
    response_text: str,
    status: str,
    latency_ms: int,
    error_code: str | None,
    error_message: str | None,
    created_at: datetime | None = None,
    include_text: bool = False,
    metadata: dict[str, Any] | None = None,
    base_dir: Path | None = None,
) -> Path:
    timestamp = _utc_timestamp(created_at)
    trace_payload = _build_telegram_trace_payload(
        trace_id=trace_id,
        request_id=request_id or trace_id,
        chat_id=chat_id,
        user_id=user_id,
        command=command,
        text_chars=len(input_text),
        response_chars=len(response_text),
        model=model,
        status=status,
        error_code=error_code,
        latency_ms=latency_ms,
        created_at=timestamp,
        include_text=include_text,
        text=input_text,
        response_text=response_text,
        error_message=error_message,
        metadata=metadata,
    )
    trace_payload = _finalize_telegram_trace_payload(trace_payload)
    resolved_base_dir = base_dir or TELEGRAM_EVAL_RUNS_DIR
    output_path = build_telegram_eval_path(
        created_at=timestamp,
        model=model,
        base_dir=resolved_base_dir,
    )
    payload = build_eval_record_from_trace(trace_payload)

    resolved_base_dir.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"[telegram_eval] wrote eval run: {output_path}")
    return output_path


def _int_list(value: Any) -> list[int]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, int)]


def _conversation_run_dir(
    *,
    created_at: datetime | None = None,
    base_dir: Path | None = None,
) -> Path:
    timestamp = _utc_timestamp(created_at)
    resolved_base_dir = base_dir or TELEGRAM_CONVERSATION_RUNS_DIR
    return resolved_base_dir / f"{timestamp:%Y-%m-%d}"


def _build_telegram_conversation_payload(
    *,
    trace_id: str,
    chat_id: int | None,
    user_id: int | None,
    command: str,
    model: str | None,
    status: str,
    error_code: str | None,
    latency_ms: int,
    created_at: datetime | None = None,
    input_text: str | None = None,
    response_text: str | None = None,
    error_message: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    timestamp = _utc_timestamp(created_at)
    source_filenames = metadata.get("source_filenames") if isinstance(metadata, dict) else None
    if not isinstance(source_filenames, list) or not all(isinstance(item, str) for item in source_filenames):
        source_filenames = []

    return {
        "trace_id": trace_id,
        "created_at": timestamp.isoformat(),
        "source": "telegram",
        "user_id": user_id,
        "chat_id": chat_id,
        "session_id": str(chat_id) if isinstance(chat_id, int) else None,
        "command": command,
        "input": input_text,
        "response": response_text,
        "model": model,
        "provider": metadata.get("provider") if isinstance(metadata, dict) else None,
        "temperature": metadata.get("temperature") if isinstance(metadata, dict) else None,
        "tokens_input": metadata.get("tokens_input") if isinstance(metadata, dict) and isinstance(metadata.get("tokens_input"), int) else None,
        "tokens_output": metadata.get("tokens_output") if isinstance(metadata, dict) and isinstance(metadata.get("tokens_output"), int) else None,
        "tokens_total": metadata.get("tokens_total") if isinstance(metadata, dict) and isinstance(metadata.get("tokens_total"), int) else None,
        "latency_ms": latency_ms,
        "retrieval_status": metadata.get("retrieval_status") if isinstance(metadata, dict) else None,
        "chunk_ids": _int_list(metadata.get("chunk_ids")) if isinstance(metadata, dict) else [],
        "document_ids": _int_list(metadata.get("document_ids")) if isinstance(metadata, dict) else [],
        "source_filenames": source_filenames,
        "status": status,
        "error_code": error_code,
        "error_message": error_message,
        "warnings": _warnings_list(metadata.get("warnings")) if isinstance(metadata, dict) else [],
    }


def write_telegram_conversation_record(
    *,
    trace_id: str,
    chat_id: int | None,
    user_id: int | None,
    command: str,
    model: str | None,
    input_text: str | None,
    response_text: str | None,
    status: str,
    latency_ms: int,
    error_code: str | None = None,
    error_message: str | None = None,
    created_at: datetime | None = None,
    metadata: dict[str, Any] | None = None,
    base_dir: Path | None = None,
) -> Path:
    timestamp = _utc_timestamp(created_at)
    output_dir = _conversation_run_dir(created_at=timestamp, base_dir=base_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{trace_id}.json"
    payload = _build_telegram_conversation_payload(
        trace_id=trace_id,
        chat_id=chat_id,
        user_id=user_id,
        command=command,
        model=model,
        status=status,
        error_code=error_code,
        latency_ms=latency_ms,
        created_at=timestamp,
        input_text=input_text,
        response_text=response_text,
        error_message=error_message,
        metadata=metadata,
    )

    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=output_dir,
            prefix=f"{trace_id}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            temp_path = Path(handle.name)

        os.replace(temp_path, output_path)
    except Exception:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink(missing_ok=True)
        raise

    return output_path


def _parse_conversation_created_at(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None

    try:
        return _utc_timestamp(datetime.fromisoformat(value))
    except ValueError:
        return None


def _load_conversation_records_report(
    base_dir: Path,
    limit: int,
) -> dict[str, Any]:
    if limit <= 0 or not base_dir.exists():
        return {
            "records": [],
            "loaded_records": 0,
            "skipped_records": 0,
            "warnings": [],
            "base_dir": str(base_dir),
        }

    loaded_items: list[tuple[datetime, str, dict[str, Any]]] = []
    skipped_records = 0
    warnings: list[str] = []

    for candidate in sorted(base_dir.rglob("*.json")):
        try:
            payload = json.loads(candidate.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            skipped_records += 1
            warnings.append(f"conversation_record_skipped path={candidate} reason={exc.__class__.__name__}")
            continue

        if not isinstance(payload, dict):
            skipped_records += 1
            warnings.append(f"conversation_record_skipped path={candidate} reason=invalid_payload_type")
            continue

        created_at = _parse_conversation_created_at(payload.get("created_at"))
        if created_at is None:
            skipped_records += 1
            warnings.append(f"conversation_record_skipped path={candidate} reason=created_at_invalid")
            continue

        loaded_items.append((created_at, str(candidate), payload))

    loaded_items.sort(key=lambda item: (item[0], item[1]))
    records = [item[2] for item in loaded_items[-limit:]]
    return {
        "records": records,
        "loaded_records": len(records),
        "skipped_records": skipped_records,
        "warnings": warnings,
        "base_dir": str(base_dir),
    }


def load_conversation_records(base_dir: Path, limit: int = 1000) -> list[dict[str, Any]]:
    return _load_conversation_records_report(base_dir=base_dir, limit=limit)["records"]


def load_conversation_records_report(base_dir: Path, limit: int = 1000) -> dict[str, Any]:
    return _load_conversation_records_report(base_dir=base_dir, limit=limit)
