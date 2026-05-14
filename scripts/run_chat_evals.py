import argparse
import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.adapters.backend_client import build_internal_auth_headers
from app.config import BACKEND_URL


DEFAULT_BACKEND_URL = BACKEND_URL
DEFAULT_TIMEOUT_SECONDS = 60
RAW_METRIC_KEYS = (
    "prompt_eval_count",
    "eval_count",
    "prompt_eval_duration",
    "eval_duration",
    "total_duration",
    "load_duration",
)
CASES_PATH = REPO_ROOT / "evals" / "cases" / "chat_cases.json"
BASELINE_PATH = REPO_ROOT / "evals" / "baselines" / "chat_baseline.json"
RUNS_DIR = REPO_ROOT / "evals" / "runs"


def build_auth_headers() -> dict[str, str]:
    return build_internal_auth_headers()


def load_cases(path: Path = CASES_PATH) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("chat_cases.json debe contener una lista")

    seen_ids: set[str] = set()
    validated_cases: list[dict[str, Any]] = []

    for case in data:
        if not isinstance(case, dict):
            raise ValueError("cada caso debe ser un objeto JSON")

        required_fields = {
            "id",
            "input",
            "expected_contains",
            "forbidden_contains",
            "max_chars",
            "min_chars",
            "notes",
        }
        missing = required_fields - set(case.keys())
        if missing:
            raise ValueError(f"caso incompleto: faltan {sorted(missing)}")

        case_id = str(case["id"]).strip()
        if not case_id:
            raise ValueError("case.id vacio")
        if case_id in seen_ids:
            raise ValueError(f"case.id duplicado: {case_id}")
        seen_ids.add(case_id)

        expected_contains = case["expected_contains"]
        forbidden_contains = case["forbidden_contains"]
        if not isinstance(expected_contains, list) or not all(isinstance(item, str) for item in expected_contains):
            raise ValueError(f"{case_id}: expected_contains debe ser lista de strings")
        if not isinstance(forbidden_contains, list) or not all(isinstance(item, str) for item in forbidden_contains):
            raise ValueError(f"{case_id}: forbidden_contains debe ser lista de strings")

        min_chars = case["min_chars"]
        max_chars = case["max_chars"]
        if not isinstance(min_chars, int) or not isinstance(max_chars, int):
            raise ValueError(f"{case_id}: min_chars y max_chars deben ser enteros")
        if min_chars < 0 or max_chars < min_chars:
            raise ValueError(f"{case_id}: rango de longitud invalido")

        validated_cases.append(
            {
                "id": case_id,
                "input": str(case["input"]),
                "expected_contains": expected_contains,
                "forbidden_contains": forbidden_contains,
                "max_chars": max_chars,
                "min_chars": min_chars,
                "notes": str(case["notes"]),
            }
        )

    return validated_cases


def generate_run_id(now: datetime | None = None) -> str:
    timestamp = now or datetime.now(timezone.utc)
    return timestamp.strftime("%Y%m%dT%H%M%SZ")


def build_case_trace_id(run_id: str, case_id: str) -> str:
    return uuid.uuid5(uuid.NAMESPACE_URL, f"locales-chat-eval:{run_id}:{case_id}").hex


def evaluate_expected_contains(answer: str, expected_contains: list[str]) -> list[str]:
    normalized_answer = answer.lower()
    return [term for term in expected_contains if term.lower() not in normalized_answer]


def evaluate_forbidden_contains(answer: str, forbidden_contains: list[str]) -> list[str]:
    normalized_answer = answer.lower()
    return [term for term in forbidden_contains if term.lower() in normalized_answer]


def evaluate_length(answer: str, min_chars: int, max_chars: int) -> dict[str, Any]:
    length = len(answer)
    return {
        "length": length,
        "min_chars": min_chars,
        "max_chars": max_chars,
        "too_short": length < min_chars,
        "too_long": length > max_chars,
        "within_range": min_chars <= length <= max_chars,
    }


def _extract_error_payload(response: requests.Response) -> tuple[str | None, str | None]:
    try:
        payload = response.json()
    except ValueError:
        return None, response.text.strip() or None

    detail = payload.get("detail", payload)
    if isinstance(detail, dict):
        return _as_string(detail.get("code")), _as_string(detail.get("message"))
    return None, _as_string(detail)


def _as_string(value: Any) -> str | None:
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned or None
    return None


def _safe_positive_rate(tokens: int | None, duration_ns: int | None) -> float | None:
    if tokens is None or duration_ns is None or duration_ns <= 0:
        return None
    return (tokens / duration_ns) * 1_000_000_000


def extract_ollama_metrics(payload: dict[str, Any]) -> dict[str, Any]:
    metrics: dict[str, int | None] = {}
    warnings: list[str] = []
    metric_failures: list[str] = []
    missing: list[str] = []

    for key in RAW_METRIC_KEYS:
        value = payload.get(key)
        if isinstance(value, int) and not isinstance(value, bool):
            metrics[key] = value
        else:
            metrics[key] = None
            if value is None:
                missing.append(key)
            else:
                warnings.append(f"metric_invalid:{key}")

    if missing:
        warnings.append("metric_missing:" + ",".join(missing))

    tokens_input = metrics["prompt_eval_count"]
    tokens_output = metrics["eval_count"]
    tokens_total = None
    if tokens_input is not None and tokens_output is not None:
        tokens_total = tokens_input + tokens_output

    if tokens_output is not None and tokens_output <= 0:
        metric_failures.append("output_tokens_non_positive")
    if metrics["total_duration"] is not None and metrics["total_duration"] <= 0:
        metric_failures.append("total_duration_non_positive")
    if tokens_output is not None and tokens_output > 0:
        if metrics["eval_duration"] is None:
            warnings.append("metric_missing:eval_duration_for_output_tokens")
        elif metrics["eval_duration"] <= 0:
            metric_failures.append("eval_duration_non_positive")

    output_tokens_per_second = _safe_positive_rate(tokens_output, metrics["eval_duration"])
    prompt_tokens_per_second = _safe_positive_rate(tokens_input, metrics["prompt_eval_duration"])

    return {
        **metrics,
        "tokens_input": tokens_input,
        "tokens_output": tokens_output,
        "tokens_total": tokens_total,
        "output_tokens_per_second": output_tokens_per_second,
        "prompt_tokens_per_second": prompt_tokens_per_second,
        "total_duration_ns": metrics["total_duration"],
        "load_duration_ns": metrics["load_duration"],
        "warnings": warnings,
        "metric_failures": metric_failures,
    }


def evaluate_chat_response(case: dict[str, Any], http_status: int, payload: dict[str, Any] | None) -> dict[str, Any]:
    payload = payload or {}
    answer = payload.get("answer") if isinstance(payload.get("answer"), str) else ""
    status = _as_string(payload.get("status")) or "error"
    expected_missing = evaluate_expected_contains(answer, case["expected_contains"])
    forbidden_present = evaluate_forbidden_contains(answer, case["forbidden_contains"])
    length_info = evaluate_length(answer, case["min_chars"], case["max_chars"])
    metrics_info = extract_ollama_metrics(payload)

    checks = {
        "http_ok": http_status == 200,
        "response_not_empty": bool(answer.strip()),
        "expected_contains": not expected_missing,
        "forbidden_contains": not forbidden_present,
        "length_bounds": length_info["within_range"],
        "metrics_valid": not metrics_info["metric_failures"],
    }

    return {
        "status": status,
        "answer": answer,
        "response_chars": len(answer),
        "expected_contains_missing": expected_missing,
        "forbidden_contains_present": forbidden_present,
        "length_check": length_info,
        "checks": checks,
        "warnings": metrics_info["warnings"],
        "metric_failures": metrics_info["metric_failures"],
        **metrics_info,
    }


def run_case(
    case: dict[str, Any],
    *,
    run_id: str,
    backend_url: str,
    timeout_seconds: int,
) -> dict[str, Any]:
    trace_id = build_case_trace_id(run_id, case["id"])
    started_at = time.perf_counter()
    response_payload: dict[str, Any] | None = None
    http_status = 0
    error_code: str | None = None
    error_message: str | None = None

    try:
        response = requests.post(
            f"{backend_url.rstrip('/')}/chat",
            headers=build_auth_headers(),
            json={
                "message": case["input"],
                "trace_id": trace_id,
            },
            timeout=timeout_seconds,
        )
        http_status = response.status_code
        try:
            response_payload = response.json()
        except ValueError:
            response_payload = None
            error_code = "invalid_json_response"
            error_message = "backend devolvio JSON invalido"

        if http_status >= 400:
            detail_code, detail_message = _extract_error_payload(response)
            error_code = detail_code or error_code or f"http_{http_status}"
            error_message = detail_message or error_message or "backend_error"
    except requests.exceptions.ConnectionError:
        error_code = "backend_unavailable"
        error_message = "no se pudo conectar al backend local"
    except requests.exceptions.Timeout:
        error_code = "backend_timeout"
        error_message = "timeout al llamar al backend local"
    except requests.exceptions.RequestException as exc:
        error_code = "backend_request_error"
        error_message = str(exc)

    client_latency_ms = int((time.perf_counter() - started_at) * 1000)
    evaluated = evaluate_chat_response(case, http_status, response_payload)
    backend_latency_ms = response_payload.get("latency_ms") if isinstance(response_payload, dict) and isinstance(response_payload.get("latency_ms"), int) else None
    passed = all(evaluated["checks"].values())
    if error_code is not None:
        passed = False

    warnings = list(evaluated["warnings"])
    if error_code == "invalid_json_response":
        warnings.append("backend_invalid_json")

    return {
        "case_id": case["id"],
        "trace_id": trace_id,
        "input": case["input"],
        "notes": case["notes"],
        "http_status": http_status,
        "status": evaluated["status"],
        "passed": passed,
        "latency_ms": backend_latency_ms if backend_latency_ms is not None else client_latency_ms,
        "client_latency_ms": client_latency_ms,
        "error_code": error_code,
        "error_message": error_message,
        "response": evaluated["answer"],
        "response_chars": evaluated["response_chars"],
        "expected_contains_missing": evaluated["expected_contains_missing"],
        "forbidden_contains_present": evaluated["forbidden_contains_present"],
        "length_check": evaluated["length_check"],
        "checks": evaluated["checks"],
        "warnings": warnings,
        "metric_failures": evaluated["metric_failures"],
        "prompt_eval_count": evaluated["prompt_eval_count"],
        "eval_count": evaluated["eval_count"],
        "prompt_eval_duration": evaluated["prompt_eval_duration"],
        "eval_duration": evaluated["eval_duration"],
        "total_duration": evaluated["total_duration"],
        "load_duration": evaluated["load_duration"],
        "tokens_input": evaluated["tokens_input"],
        "tokens_output": evaluated["tokens_output"],
        "tokens_total": evaluated["tokens_total"],
        "output_tokens_per_second": evaluated["output_tokens_per_second"],
        "prompt_tokens_per_second": evaluated["prompt_tokens_per_second"],
        "total_duration_ns": evaluated["total_duration_ns"],
        "load_duration_ns": evaluated["load_duration_ns"],
        "min_chars": case["min_chars"],
        "max_chars": case["max_chars"],
        "model": _as_string(response_payload.get("model")) if isinstance(response_payload, dict) else None,
    }


def aggregate_run_metrics(results: list[dict[str, Any]]) -> dict[str, Any]:
    def total_for(key: str) -> int:
        return sum(value for value in (result.get(key) for result in results) if isinstance(value, int))

    prompt_tokens_total = total_for("tokens_input")
    output_tokens_total = total_for("tokens_output")
    tokens_total = total_for("tokens_total")
    prompt_eval_duration_total = total_for("prompt_eval_duration")
    eval_duration_total = total_for("eval_duration")
    total_duration_total = total_for("total_duration")
    load_duration_total = total_for("load_duration")

    warning_count = sum(len(result.get("warnings", [])) for result in results)
    metric_failure_count = sum(len(result.get("metric_failures", [])) for result in results)

    return {
        "tokens_input_total": prompt_tokens_total,
        "tokens_output_total": output_tokens_total,
        "tokens_total_total": tokens_total,
        "prompt_eval_duration_total_ns": prompt_eval_duration_total,
        "eval_duration_total_ns": eval_duration_total,
        "total_duration_total_ns": total_duration_total,
        "load_duration_total_ns": load_duration_total,
        "output_tokens_per_second_overall": _safe_positive_rate(output_tokens_total, eval_duration_total),
        "prompt_tokens_per_second_overall": _safe_positive_rate(prompt_tokens_total, prompt_eval_duration_total),
        "warnings_total": warning_count,
        "metric_failures_total": metric_failure_count,
    }


def compare_case_against_baseline(current: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    changes: list[dict[str, Any]] = []

    if current.get("status") != baseline.get("status"):
        changes.append({"type": "status_changed", "baseline": baseline.get("status"), "current": current.get("status")})

    if bool(current.get("passed")) != bool(baseline.get("passed")):
        changes.append({"type": "pass_fail_changed", "baseline": baseline.get("passed"), "current": current.get("passed")})

    baseline_length = baseline.get("response_chars")
    current_length = current.get("response_chars")
    if isinstance(baseline_length, int) and baseline_length > 0 and isinstance(current_length, int):
        if abs(current_length - baseline_length) / baseline_length > 0.40:
            changes.append({"type": "length_changed_over_40_percent", "baseline": baseline_length, "current": current_length})

    if not _as_string(current.get("response")):
        changes.append({"type": "response_empty"})

    baseline_forbidden = set(baseline.get("forbidden_contains_present", []))
    current_forbidden = set(current.get("forbidden_contains_present", []))
    new_forbidden = sorted(current_forbidden - baseline_forbidden)
    if new_forbidden:
        changes.append({"type": "new_forbidden_terms", "terms": new_forbidden})

    baseline_latency = baseline.get("latency_ms")
    current_latency = current.get("latency_ms")
    if isinstance(baseline_latency, int) and baseline_latency > 0 and isinstance(current_latency, int):
        if current_latency > baseline_latency * 2:
            changes.append({"type": "latency_changed_over_100_percent", "baseline": baseline_latency, "current": current_latency})

    baseline_prompt_tokens = baseline.get("tokens_input")
    current_prompt_tokens = current.get("tokens_input")
    if isinstance(baseline_prompt_tokens, int) and baseline_prompt_tokens > 0 and isinstance(current_prompt_tokens, int):
        if current_prompt_tokens > baseline_prompt_tokens * 1.5:
            changes.append({"type": "prompt_tokens_increase_over_50_percent", "baseline": baseline_prompt_tokens, "current": current_prompt_tokens})

    baseline_output_tokens = baseline.get("tokens_output")
    current_output_tokens = current.get("tokens_output")
    if isinstance(baseline_output_tokens, int) and baseline_output_tokens > 0 and isinstance(current_output_tokens, int):
        if current_output_tokens > baseline_output_tokens * 2:
            changes.append({"type": "output_tokens_increase_over_100_percent", "baseline": baseline_output_tokens, "current": current_output_tokens})

    baseline_output_tps = baseline.get("output_tokens_per_second")
    current_output_tps = current.get("output_tokens_per_second")
    if isinstance(baseline_output_tps, (int, float)) and baseline_output_tps > 0 and isinstance(current_output_tps, (int, float)):
        if current_output_tps < baseline_output_tps * 0.5:
            changes.append({"type": "output_tokens_per_second_degraded_over_50_percent", "baseline": baseline_output_tps, "current": current_output_tps})

    baseline_prompt_tps = baseline.get("prompt_tokens_per_second")
    current_prompt_tps = current.get("prompt_tokens_per_second")
    if isinstance(baseline_prompt_tps, (int, float)) and baseline_prompt_tps > 0 and isinstance(current_prompt_tps, (int, float)):
        if current_prompt_tps < baseline_prompt_tps * 0.5:
            changes.append({"type": "prompt_tokens_per_second_degraded_over_50_percent", "baseline": baseline_prompt_tps, "current": current_prompt_tps})

    baseline_total_duration = baseline.get("total_duration_ns") or baseline.get("total_duration")
    current_total_duration = current.get("total_duration_ns") or current.get("total_duration")
    if isinstance(baseline_total_duration, int) and baseline_total_duration > 0 and isinstance(current_total_duration, int):
        if current_total_duration > baseline_total_duration * 2:
            changes.append({"type": "total_duration_increase_over_100_percent", "baseline": baseline_total_duration, "current": current_total_duration})

    max_chars = current.get("max_chars")
    if isinstance(current_length, int) and isinstance(max_chars, int) and current_length > max_chars:
        changes.append({"type": "response_extremely_long", "current": current_length, "max_chars": max_chars})

    return {
        "case_id": current["case_id"],
        "changed": bool(changes),
        "changes": changes,
    }


def compare_against_baseline(current_run: dict[str, Any], baseline_run: dict[str, Any]) -> dict[str, Any]:
    baseline_results = baseline_run.get("results", [])
    if not isinstance(baseline_results, list) or not baseline_results:
        return {
            "baseline_available": False,
            "warning": "baseline vacio; ejecutar --write-baseline primero",
            "cases_compared": 0,
            "cases_with_changes": 0,
            "comparisons": [],
        }

    baseline_by_case = {result["case_id"]: result for result in baseline_results if isinstance(result, dict) and "case_id" in result}
    comparisons = []
    for current in current_run["results"]:
        baseline = baseline_by_case.get(current["case_id"])
        if baseline is None:
            comparisons.append(
                {
                    "case_id": current["case_id"],
                    "changed": True,
                    "changes": [{"type": "baseline_case_missing"}],
                }
            )
            continue
        comparisons.append(compare_case_against_baseline(current, baseline))

    return {
        "baseline_available": True,
        "cases_compared": len(comparisons),
        "cases_with_changes": sum(1 for item in comparisons if item["changed"]),
        "comparisons": comparisons,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_evals(*, write_baseline: bool = False, compare_baseline: bool = False) -> dict[str, Any]:
    backend_url = os.getenv("BACKEND_URL", os.getenv("LOCALES_BACKEND_URL", DEFAULT_BACKEND_URL)).rstrip("/")
    eval_timeout_seconds = int(os.getenv("EVAL_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT_SECONDS)))
    configured_model = os.getenv("OLLAMA_MODEL") or None

    cases = load_cases()
    run_id = generate_run_id()
    created_at = datetime.now(timezone.utc).isoformat()
    results = [run_case(case, run_id=run_id, backend_url=backend_url, timeout_seconds=eval_timeout_seconds) for case in cases]
    passed = sum(1 for result in results if result["passed"])
    failed = len(results) - passed

    run_payload = {
        "version": 1,
        "run_id": run_id,
        "created_at": created_at,
        "backend_url": backend_url,
        "model": configured_model or next((result.get("model") for result in results if result.get("model")), None),
        "cases_total": len(results),
        "cases_passed": passed,
        "cases_failed": failed,
        "metrics_summary": aggregate_run_metrics(results),
        "results": results,
    }
    run_payload["baseline_written"] = False

    if compare_baseline:
        baseline_payload = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
        run_payload["baseline_comparison"] = compare_against_baseline(run_payload, baseline_payload)

    output_path = RUNS_DIR / f"chat_eval_{run_id}.json"
    write_json(output_path, run_payload)
    run_payload["output_path"] = str(output_path)

    if write_baseline and failed == 0:
        write_json(BASELINE_PATH, run_payload)
        run_payload["baseline_written"] = True

    return run_payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run deterministic chat evals against local FastAPI /chat")
    parser.add_argument("--write-baseline", action="store_true", help="write current run to evals/baselines/chat_baseline.json")
    parser.add_argument("--compare-baseline", action="store_true", help="compare current run against evals/baselines/chat_baseline.json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_payload = run_evals(write_baseline=args.write_baseline, compare_baseline=args.compare_baseline)

    print(f"run_id={run_payload['run_id']}")
    print(f"cases_total={run_payload['cases_total']}")
    print(f"cases_passed={run_payload['cases_passed']}")
    print(f"cases_failed={run_payload['cases_failed']}")
    print(f"output_path={run_payload['output_path']}")

    if args.compare_baseline:
        comparison = run_payload.get("baseline_comparison", {})
        if comparison.get("baseline_available"):
            print(f"baseline_cases_with_changes={comparison['cases_with_changes']}")
        else:
            print(f"baseline_warning={comparison.get('warning')}")

    if args.write_baseline:
        if run_payload["baseline_written"]:
            print(f"baseline_written={BASELINE_PATH}")
        else:
            print("baseline_written=skipped_failed_run")

    return 0 if run_payload["cases_failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
