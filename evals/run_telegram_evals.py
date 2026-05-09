import json
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import requests


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.schemas import ChatRequest


DEFAULT_TEMPERATURES = [0.2, 0.7, 1.0]
DEFAULT_RUNS_PER_TEMPERATURE = 5
DEFAULT_ENDPOINT = "http://127.0.0.1:8000/chat"
DEFAULT_TIMEOUT_SECONDS = 60
RUNS_ROOT = REPO_ROOT / "evals" / "runs"
FIXED_SOURCE = "telegram_eval"
FIXED_COMMAND = "eval"
FIXED_USE_RAG = True
FIXED_TOP_K = 3
NUCLEO_ALLOWED_SOURCE_FILENAMES = [
    "EVOLUTION_MAP.md",
    "ARCHITECTURE.md",
    "CONTRACT_POLICY_TOOLREGISTRY.md",
    "orchestrator.md",
    "planner.md",
    "agent_service.md",
]
INITIAL_CASES = [
    {
        "case_id": "orchestrator_function_001",
        "input": "¿Qué función tiene el orquestador?",
        "expected_terms": ["AgentRuntime", "orquestador", "producción"],
        "allowed_source_filenames": NUCLEO_ALLOWED_SOURCE_FILENAMES,
        "expected_source_filenames": ["EVOLUTION_MAP.md"],
        "forbidden_source_filenames": ["MEMORIA 27.12.2021.pdf", "CVjgo.pdf"],
        "forbidden_terms": [
            "supervisor de producción",
            "API, runtime y tools de producción",
            "estado actual verificado",
        ],
        "max_forbidden_terms": 0,
    }
]
YES_VALUES = {"s", "si", "sí", "y", "yes"}
HEAVY_RAG_FIELDS = {
    "context",
    "rag_context",
    "evidence",
    "evidence_text",
    "evidence_package",
    "prompt",
    "full_prompt",
    "system_prompt",
    "messages",
    "chunks",
    "retrieved_chunks",
    "documents",
    "raw_chunks",
    "chunk_texts",
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def build_timestamp(now: datetime | None = None) -> str:
    current = now or utc_now()
    return current.strftime("%Y%m%dT%H%M%S%fZ")


def detect_message_field() -> str:
    field_names = tuple(ChatRequest.model_fields.keys())
    for candidate in ("message", "text", "input"):
        if candidate in field_names:
            return candidate
    raise ValueError(f"chat_request_message_field_missing:{field_names}")


def parse_temperatures(raw_value: str, default: list[float] | None = None) -> list[float]:
    fallback = list(default or DEFAULT_TEMPERATURES)
    cleaned = raw_value.strip()
    if not cleaned:
        return fallback

    values: list[float] = []
    for item in cleaned.split(","):
        candidate = item.strip()
        if not candidate:
            raise ValueError("temperatures_empty_item")
        try:
            temperature = float(candidate)
        except ValueError as exc:
            raise ValueError(f"temperature_invalid:{candidate}") from exc
        if not 0.0 <= temperature <= 1.0:
            raise ValueError(f"temperature_out_of_range:{candidate}")
        values.append(temperature)

    if not values:
        raise ValueError("temperatures_required")
    return values


def parse_runs_per_temperature(raw_value: str, default: int = DEFAULT_RUNS_PER_TEMPERATURE) -> int:
    cleaned = raw_value.strip()
    if not cleaned:
        return default
    try:
        value = int(cleaned)
    except ValueError as exc:
        raise ValueError("runs_per_temperature_invalid") from exc
    if value <= 0:
        raise ValueError("runs_per_temperature_must_be_positive")
    return value


def is_confirmation_positive(raw_value: str) -> bool:
    return raw_value.strip().lower() in YES_VALUES


def extract_response_text(payload: dict[str, Any]) -> str:
    for key in ("response", "answer"):
        value = payload.get(key)
        if isinstance(value, str):
            return value
    return ""


def evaluate_response(case: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    response_text = extract_response_text(payload)
    normalized_response = response_text.lower()

    missing_expected_terms = [
        term for term in case["expected_terms"] if term.lower() not in normalized_response
    ]
    forbidden_terms_found = [
        term for term in case["forbidden_terms"] if term.lower() in normalized_response
    ]

    retrieval_ok = payload.get("retrieval_status") == "EVIDENCE_FOUND"
    status_ok = payload.get("status") == "ok"
    chunk_ids = payload.get("chunk_ids")
    chunk_ids_ok = isinstance(chunk_ids, list) and len(chunk_ids) > 0

    source_filenames_found = payload.get("source_filenames", [])
    normalized_source_filenames = []
    if isinstance(source_filenames_found, list):
        for item in source_filenames_found:
            source_filename = _extract_source_filename(item)
            if source_filename and source_filename not in normalized_source_filenames:
                normalized_source_filenames.append(source_filename)

    expected_source_filenames = [
        source_filename
        for source_filename in (
            _extract_source_filename(item) for item in case.get("expected_source_filenames", [])
        )
        if source_filename
    ]
    forbidden_source_filenames = [
        source_filename
        for source_filename in (
            _extract_source_filename(item) for item in case.get("forbidden_source_filenames", [])
        )
        if source_filename
    ]
    forbidden_sources_found = [
        source_filename
        for source_filename in normalized_source_filenames
        if source_filename in forbidden_source_filenames
    ]
    retrieval_source_ok = len(forbidden_sources_found) == 0

    if not expected_source_filenames:
        source_filename_match = "not_configured"
    elif normalized_source_filenames:
        source_filename_match: bool | str | None = any(
            expected_filename in normalized_source_filenames
            for expected_filename in expected_source_filenames
        )
    else:
        source_filename_match = "not_available"

    forbidden_terms_ok = len(forbidden_terms_found) <= int(case.get("max_forbidden_terms", 0))

    if (
        not retrieval_ok
        or not status_ok
        or not chunk_ids_ok
        or forbidden_sources_found
        or source_filename_match is False
    ):
        drift_score = 3
    elif forbidden_terms_found:
        drift_score = 2
    elif missing_expected_terms:
        drift_score = 1
    else:
        drift_score = 0

    passed = (
        status_ok
        and retrieval_ok
        and chunk_ids_ok
        and retrieval_source_ok
        and not missing_expected_terms
        and not forbidden_terms_found
        and source_filename_match is not False
    )

    return {
        "pass": passed,
        "drift_score": drift_score,
        "status_ok": status_ok,
        "retrieval_ok": retrieval_ok,
        "chunk_ids_ok": chunk_ids_ok,
        "retrieval_source_ok": retrieval_source_ok,
        "source_filename_match": source_filename_match,
        "source_filenames_found": normalized_source_filenames,
        "forbidden_sources_found": forbidden_sources_found,
        "missing_expected_terms": missing_expected_terms,
        "forbidden_terms_found": forbidden_terms_found,
        "forbidden_terms_ok": forbidden_terms_ok,
        "response_chars": len(response_text),
    }


def _normalize_model_for_path(model: str) -> str:
    normalized = model.strip()
    for source, target in (("/", "-"), ("\\", "-"), (" ", "_"), (":", "-")):
        normalized = normalized.replace(source, target)
    return normalized or "model"


def make_output_dir(
    output_root: Path,
    timestamp: str,
    model: str,
) -> Path:
    safe_model = _normalize_model_for_path(model)
    return output_root / f"telegram_eval_{safe_model}_{timestamp}"


def _normalize_chunk_id(value: Any) -> int | str | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        cleaned = value.strip()
        if not cleaned:
            return None
        if cleaned.isdigit():
            return int(cleaned)
        return cleaned
    return None


def _extract_source_filename(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    return Path(cleaned).name


def _collect_chunk_metadata_from_item(
    item: Any,
    *,
    chunk_ids: list[int | str],
    source_filenames: list[str],
    scores: list[float],
) -> None:
    if isinstance(item, list):
        for child in item:
            _collect_chunk_metadata_from_item(
                child,
                chunk_ids=chunk_ids,
                source_filenames=source_filenames,
                scores=scores,
            )
        return

    if not isinstance(item, dict):
        return

    normalized_chunk_id = _normalize_chunk_id(item.get("id"))
    if normalized_chunk_id is not None and normalized_chunk_id not in chunk_ids:
        chunk_ids.append(normalized_chunk_id)

    for key in ("filename", "source_filename", "document_name", "source_path"):
        source_filename = _extract_source_filename(item.get(key))
        if source_filename and source_filename not in source_filenames:
            source_filenames.append(source_filename)

    metadata = item.get("metadata")
    if isinstance(metadata, dict):
        _collect_chunk_metadata_from_item(
            metadata,
            chunk_ids=chunk_ids,
            source_filenames=source_filenames,
            scores=scores,
        )

    for key in ("score", "similarity", "relevance_score"):
        value = item.get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            numeric_value = float(value)
            if numeric_value not in scores:
                scores.append(numeric_value)


def sanitize_trace_for_eval_record(record: dict[str, Any]) -> dict[str, Any]:
    sanitized = dict(record)
    sanitized_fields: list[str] = []

    chunk_ids: list[int | str] = []
    existing_chunk_ids = sanitized.get("chunk_ids")
    if isinstance(existing_chunk_ids, list):
        for item in existing_chunk_ids:
            normalized_chunk_id = _normalize_chunk_id(item)
            if normalized_chunk_id is not None and normalized_chunk_id not in chunk_ids:
                chunk_ids.append(normalized_chunk_id)

    source_filenames: list[str] = []
    existing_source_filenames = sanitized.get("source_filenames")
    if isinstance(existing_source_filenames, list):
        for item in existing_source_filenames:
            source_filename = _extract_source_filename(item)
            if source_filename and source_filename not in source_filenames:
                source_filenames.append(source_filename)

    scores: list[float] = []
    existing_scores = sanitized.get("scores")
    if isinstance(existing_scores, list):
        for item in existing_scores:
            if isinstance(item, (int, float)) and not isinstance(item, bool):
                numeric_value = float(item)
                if numeric_value not in scores:
                    scores.append(numeric_value)

    for field_name in HEAVY_RAG_FIELDS:
        if field_name not in sanitized:
            continue

        field_value = sanitized[field_name]
        if field_name in {"chunks", "retrieved_chunks", "documents", "raw_chunks", "chunk_texts", "evidence_package"}:
            _collect_chunk_metadata_from_item(
                field_value,
                chunk_ids=chunk_ids,
                source_filenames=source_filenames,
                scores=scores,
            )

        sanitized.pop(field_name, None)
        sanitized_fields.append(field_name)

    if chunk_ids:
        sanitized["chunk_ids"] = chunk_ids
    if source_filenames:
        sanitized["source_filenames"] = source_filenames
    if scores and "scores" not in sanitized:
        sanitized["scores"] = scores

    if sanitized_fields:
        sanitized["sanitized_fields"] = sorted(sanitized_fields)
        sanitized["rag_payload_sanitized"] = True

    return sanitized


def prompt_until_valid(
    prompt: str,
    *,
    input_fn: Callable[[str], str],
    print_fn: Callable[..., None] = print,
    parse_fn: Callable[[str], Any] | None = None,
    allow_empty: bool = False,
    error_message: str,
) -> Any:
    while True:
        value = input_fn(prompt)
        if allow_empty or value.strip():
            try:
                return parse_fn(value) if parse_fn is not None else value.strip()
            except ValueError as exc:
                print_fn(f"{error_message}: {exc}")
                continue
        print_fn(error_message)


def collect_configuration(
    *,
    input_fn: Callable[[str], str] = input,
    print_fn: Callable[..., None] = print,
    now: datetime | None = None,
) -> dict[str, Any]:
    model = prompt_until_valid(
        "Modelo a evaluar: ",
        input_fn=input_fn,
        print_fn=print_fn,
        error_message="El modelo es obligatorio",
    )
    temperatures = prompt_until_valid(
        "Temperaturas [default: 0.2,0.7,1.0]: ",
        input_fn=input_fn,
        print_fn=print_fn,
        parse_fn=lambda raw: parse_temperatures(raw, DEFAULT_TEMPERATURES),
        allow_empty=True,
        error_message="Temperaturas inválidas",
    )
    runs_per_temperature = prompt_until_valid(
        "Runs por temperatura [default: 5]: ",
        input_fn=input_fn,
        print_fn=print_fn,
        parse_fn=parse_runs_per_temperature,
        allow_empty=True,
        error_message="Runs por temperatura inválido",
    )
    endpoint = prompt_until_valid(
        f"Endpoint [default: {DEFAULT_ENDPOINT}]: ",
        input_fn=input_fn,
        print_fn=print_fn,
        parse_fn=lambda raw: raw.strip() or DEFAULT_ENDPOINT,
        allow_empty=True,
        error_message="Endpoint inválido",
    )
    timestamp = build_timestamp(now)
    output_dir = make_output_dir(RUNS_ROOT, timestamp, model)

    return {
        "model": model,
        "temperatures": temperatures,
        "runs_per_temperature": runs_per_temperature,
        "endpoint": endpoint,
        "timestamp": timestamp,
        "output_dir": output_dir,
        "message_field": detect_message_field(),
        "use_rag": FIXED_USE_RAG,
        "top_k": FIXED_TOP_K,
        "source": FIXED_SOURCE,
        "command": FIXED_COMMAND,
    }


def build_summary_preview(config: dict[str, Any], cases: list[dict[str, Any]]) -> str:
    total_calls = len(cases) * len(config["temperatures"]) * config["runs_per_temperature"]
    relative_output_dir = config["output_dir"].relative_to(REPO_ROOT)
    return "\n".join(
        [
            "Resumen de evaluación:",
            f"- Modelo: {config['model']}",
            f"- Endpoint: {config['endpoint']}",
            f"- Temperaturas: {config['temperatures']}",
            f"- Runs por temperatura: {config['runs_per_temperature']}",
            f"- Casos: {len(cases)}",
            f"- Total de llamadas: {total_calls}",
            f"- top_k: {config['top_k']}",
            f"- use_rag: {str(config['use_rag']).lower()}",
            f"- Carpeta destino: {relative_output_dir}/",
        ]
    )


def build_request_payload(
    *,
    case: dict[str, Any],
    model: str,
    temperature: float,
    message_field: str,
) -> dict[str, Any]:
    payload = {
        message_field: case["input"],
        "model": model,
        "temperature": temperature,
        "use_rag": FIXED_USE_RAG,
        "top_k": FIXED_TOP_K,
        "source": FIXED_SOURCE,
        "command": FIXED_COMMAND,
    }
    allowed_source_filenames = case.get("allowed_source_filenames")
    if isinstance(allowed_source_filenames, list) and allowed_source_filenames:
        payload["allowed_source_filenames"] = allowed_source_filenames
    return payload


def call_chat_endpoint(
    *,
    endpoint: str,
    payload: dict[str, Any],
    timeout_seconds: int,
    post_fn: Callable[..., Any],
) -> tuple[int, dict[str, Any]]:
    started_at = time.perf_counter()
    try:
        response = post_fn(endpoint, json=payload, timeout=timeout_seconds)
        http_status = int(getattr(response, "status_code", 0))
        try:
            response_payload = response.json()
        except ValueError:
            response_payload = {
                "status": "error",
                "error_message": "backend devolvio JSON invalido",
                "raw_response_text": getattr(response, "text", ""),
            }
        if not isinstance(response_payload, dict):
            response_payload = {
                "status": "error",
                "error_message": "backend devolvio un payload no compatible",
                "raw_response": response_payload,
            }
    except requests.exceptions.Timeout:
        http_status = 0
        response_payload = {
            "status": "error",
            "error_message": "timeout al llamar al backend",
        }
    except requests.exceptions.ConnectionError:
        http_status = 0
        response_payload = {
            "status": "error",
            "error_message": "no se pudo conectar al backend",
        }
    except requests.exceptions.RequestException as exc:
        http_status = 0
        response_payload = {
            "status": "error",
            "error_message": str(exc),
        }

    detail = response_payload.get("detail")
    if isinstance(detail, dict):
        if isinstance(detail.get("status"), str):
            response_payload.setdefault("status", detail["status"])
        if isinstance(detail.get("message"), str):
            response_payload.setdefault("error_message", detail["message"])

    client_latency_ms = int((time.perf_counter() - started_at) * 1000)
    response_payload.setdefault("latency_ms", client_latency_ms)
    response_payload.setdefault("status", "error")
    return http_status, response_payload


def build_run_record(
    *,
    case: dict[str, Any],
    config: dict[str, Any],
    temperature: float,
    repetition_index: int,
    http_status: int,
    response_payload: dict[str, Any],
) -> dict[str, Any]:
    record = dict(response_payload)
    record.setdefault("input", case["input"])
    record.setdefault("model", config["model"])
    record.setdefault("temperature", temperature)
    record.setdefault("use_rag", config["use_rag"])
    record.setdefault("top_k", config["top_k"])
    record.setdefault("source", config["source"])
    record.setdefault("command", config["command"])
    record.setdefault("created_at", utc_now().isoformat())
    record.setdefault("response", extract_response_text(record))
    record["http_status"] = http_status
    record = sanitize_trace_for_eval_record(record)
    record["eval_case_id"] = case["case_id"]
    record["eval_run_id"] = f"{case['case_id']}__t{temperature}__r{repetition_index}"
    record["eval_temperature"] = temperature
    record["eval_result"] = evaluate_response(case, record)
    return record


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def average_for(records: list[dict[str, Any]], key: str) -> float | None:
    values = [
        float(record[key])
        for record in records
        if isinstance(record.get(key), (int, float)) and not isinstance(record.get(key), bool)
    ]
    if not values:
        return None
    return round(sum(values) / len(values), 2)


def build_summary(
    *,
    records: list[dict[str, Any]],
    config: dict[str, Any],
    created_at: str,
    cases_count: int,
) -> dict[str, Any]:
    grouped_by_temperature: list[dict[str, Any]] = []

    for temperature in config["temperatures"]:
        temperature_records = [
            record for record in records if record.get("eval_temperature") == temperature
        ]
        retrieval_status_counts = Counter(
            str(record.get("retrieval_status", "unknown")) for record in temperature_records
        )
        status_counts = Counter(str(record.get("status", "unknown")) for record in temperature_records)
        pass_count = sum(
            1 for record in temperature_records if bool(record.get("eval_result", {}).get("pass"))
        )
        forbidden_terms_total = sum(
            len(record.get("eval_result", {}).get("forbidden_terms_found", []))
            for record in temperature_records
        )
        forbidden_sources_total = sum(
            len(record.get("eval_result", {}).get("forbidden_sources_found", []))
            for record in temperature_records
        )
        source_match_failures = sum(
            1
            for record in temperature_records
            if record.get("eval_result", {}).get("source_filename_match") is False
        )
        retrieval_source_failures = sum(
            1
            for record in temperature_records
            if record.get("eval_result", {}).get("retrieval_source_ok") is False
        )
        drift_scores = [
            record.get("eval_result", {}).get("drift_score")
            for record in temperature_records
            if isinstance(record.get("eval_result", {}).get("drift_score"), int)
        ]
        avg_drift_score = round(sum(drift_scores) / len(drift_scores), 2) if drift_scores else None

        grouped_by_temperature.append(
            {
                "temperature": temperature,
                "runs": len(temperature_records),
                "pass_rate": round(pass_count / len(temperature_records), 4)
                if temperature_records
                else 0.0,
                "avg_drift_score": avg_drift_score,
                "forbidden_terms_total": forbidden_terms_total,
                "forbidden_sources_total": forbidden_sources_total,
                "source_match_failures": source_match_failures,
                "retrieval_source_failures": retrieval_source_failures,
                "avg_latency_ms": average_for(temperature_records, "latency_ms"),
                "avg_tokens_input": average_for(temperature_records, "tokens_input"),
                "avg_tokens_output": average_for(temperature_records, "tokens_output"),
                "avg_tokens_total": average_for(temperature_records, "tokens_total"),
                "retrieval_status_counts": dict(retrieval_status_counts),
                "status_counts": dict(status_counts),
            }
        )

    return {
        "model": config["model"],
        "endpoint": config["endpoint"],
        "created_at": created_at,
        "cases_count": cases_count,
        "runs_per_temperature": config["runs_per_temperature"],
        "temperatures": config["temperatures"],
        "total_runs": len(records),
        "grouped_by_temperature": grouped_by_temperature,
    }


def render_summary_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Telegram eval summary",
        "",
        f"- model: `{summary['model']}`",
        f"- endpoint: `{summary['endpoint']}`",
        f"- created_at: `{summary['created_at']}`",
        f"- total_runs: `{summary['total_runs']}`",
        "",
        "| model | temperature | runs | pass_rate | avg_drift_score | forbidden_terms_total | forbidden_sources_total | source_match_failures | retrieval_source_failures | avg_latency_ms | avg_tokens_total |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for group in summary["grouped_by_temperature"]:
        pass_rate_percent = f"{group['pass_rate'] * 100:.2f}%"
        avg_drift_score = "" if group["avg_drift_score"] is None else str(group["avg_drift_score"])
        avg_latency_ms = "" if group["avg_latency_ms"] is None else str(group["avg_latency_ms"])
        avg_tokens_total = "" if group["avg_tokens_total"] is None else str(group["avg_tokens_total"])
        lines.append(
            f"| {summary['model']} | {group['temperature']} | {group['runs']} | "
            f"{pass_rate_percent} | {avg_drift_score} | {group['forbidden_terms_total']} | "
            f"{group['forbidden_sources_total']} | {group['source_match_failures']} | "
            f"{group['retrieval_source_failures']} | {avg_latency_ms} | {avg_tokens_total} |"
        )
    lines.append("")
    return "\n".join(lines)


def execute_evaluation(
    *,
    config: dict[str, Any],
    cases: list[dict[str, Any]] | None = None,
    post_fn: Callable[..., Any] = requests.post,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    output_root: Path = RUNS_ROOT,
) -> dict[str, Any]:
    active_cases = cases or INITIAL_CASES
    output_dir = make_output_dir(
        output_root,
        config["timestamp"],
        config["model"],
    )
    output_dir.mkdir(parents=True, exist_ok=False)

    records: list[dict[str, Any]] = []
    for case in active_cases:
        for temperature in config["temperatures"]:
            for repetition_index in range(1, config["runs_per_temperature"] + 1):
                payload = build_request_payload(
                    case=case,
                    model=config["model"],
                    temperature=temperature,
                    message_field=config["message_field"],
                )
                http_status, response_payload = call_chat_endpoint(
                    endpoint=config["endpoint"],
                    payload=payload,
                    timeout_seconds=timeout_seconds,
                    post_fn=post_fn,
                )
                records.append(
                    build_run_record(
                        case=case,
                        config=config,
                        temperature=temperature,
                        repetition_index=repetition_index,
                        http_status=http_status,
                        response_payload=response_payload,
                    )
                )

    created_at = utc_now().isoformat()
    summary = build_summary(
        records=records,
        config=config,
        created_at=created_at,
        cases_count=len(active_cases),
    )
    runs_path = output_dir / "runs.jsonl"
    summary_json_path = output_dir / "summary.json"
    summary_md_path = output_dir / "summary.md"

    write_jsonl(runs_path, records)
    write_json(summary_json_path, summary)
    summary_md_path.write_text(render_summary_markdown(summary), encoding="utf-8")

    return {
        "output_dir": output_dir,
        "runs_path": runs_path,
        "summary_json_path": summary_json_path,
        "summary_md_path": summary_md_path,
        "summary": summary,
        "records": records,
    }


def run_interactive(
    *,
    input_fn: Callable[[str], str] = input,
    print_fn: Callable[..., None] = print,
    post_fn: Callable[..., Any] = requests.post,
    now: datetime | None = None,
    output_root: Path = RUNS_ROOT,
) -> dict[str, Any]:
    config = collect_configuration(input_fn=input_fn, print_fn=print_fn, now=now)
    print_fn(build_summary_preview(config, INITIAL_CASES))
    confirmation = input_fn("¿Lanzar evaluación? [s/N]: ")

    if not is_confirmation_positive(confirmation):
        print_fn("Evaluación cancelada. No se ha llamado al backend.")
        return {"cancelled": True, "config": config}

    result = execute_evaluation(
        config=config,
        post_fn=post_fn,
        output_root=output_root,
    )
    print_fn(f"Evaluación completada. Resultados en: {result['output_dir']}")
    return {"cancelled": False, **result}


def main() -> int:
    run_interactive()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
