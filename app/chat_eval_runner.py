from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import requests


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE_URL = "http://127.0.0.1:8000"
DEFAULT_CASES_PATH = "evals/cases/chat_cases.json"
DEFAULT_BASELINE_PATH = "evals/baselines/chat_baseline.json"
DEFAULT_OUT_DIR = "evals/runs"
DEFAULT_TIMEOUT = 120
RUN_VERSION = "chat_eval_run.v1"
FRONT_CHAT_RUN_VERSION = "front_chat_run.v1"


class RunnerConfigError(Exception):
    pass


class BackendUnavailableError(Exception):
    pass


RequestCaseFn = Callable[[dict[str, Any]], dict[str, Any]]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def repo_path(path_str: str) -> Path:
    candidate = Path(path_str)
    if candidate.is_absolute():
        return candidate
    return REPO_ROOT / candidate


def load_json_file(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RunnerConfigError(f"missing_file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RunnerConfigError(f"invalid_json: {path}: {exc}") from exc

    if not isinstance(payload, dict):
        raise RunnerConfigError(f"invalid_json_object: {path}")
    return payload


def load_cases(path: Path) -> list[dict[str, Any]]:
    payload = load_json_file(path)
    cases = payload.get("cases")
    if not isinstance(cases, list):
        raise RunnerConfigError(f"invalid_cases_list: {path}")
    return [case for case in cases if isinstance(case, dict)]


def load_baseline(path: Path) -> list[dict[str, Any]]:
    payload = load_json_file(path)
    baseline_items = payload.get("baseline_items")
    if not isinstance(baseline_items, list):
        raise RunnerConfigError(f"invalid_baseline_items: {path}")
    return [item for item in baseline_items if isinstance(item, dict)]


def validate_baseline_case_ids(
    cases: list[dict[str, Any]],
    baseline_items: list[dict[str, Any]],
) -> None:
    case_ids = {case.get("id") for case in cases if isinstance(case.get("id"), str)}
    missing_case_ids = [
        item.get("case_id")
        for item in baseline_items
        if isinstance(item.get("case_id"), str) and item.get("case_id") not in case_ids
    ]
    if missing_case_ids:
        joined = ", ".join(sorted(set(missing_case_ids)))
        raise RunnerConfigError(f"baseline_case_ids_not_found: {joined}")


def build_case_index(cases: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for case in cases:
        case_id = case.get("id")
        if isinstance(case_id, str) and case_id not in index:
            index[case_id] = case
    return index


def build_baseline_index(baseline_items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for item in baseline_items:
        case_id = item.get("case_id")
        if isinstance(case_id, str) and case_id not in index:
            index[case_id] = item
    return index


def build_chat_payload(case: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(case.get("input"), str) or not case["input"].strip():
        raise RunnerConfigError(f"case_input_invalid: {case.get('id')}")

    payload: dict[str, Any] = {
        "message": case["input"],
        "use_rag": case.get("use_rag", True),
    }
    for field_name in ("model", "provider", "temperature", "max_tokens"):
        value = case.get(field_name)
        if value is not None:
            payload[field_name] = value
    return payload


def extract_response_text(payload: dict[str, Any]) -> str:
    for field_name in ("response", "answer", "message", "output"):
        value = payload.get(field_name)
        if isinstance(value, str):
            return value
    return ""


def normalize_chat_result(payload: dict[str, Any], *, http_status: int) -> dict[str, Any]:
    source = payload
    if http_status >= 400 and isinstance(payload.get("detail"), dict):
        source = payload["detail"]

    response_text = extract_response_text(source)
    tokens_input = source.get("tokens_input")
    tokens_output = source.get("tokens_output")
    tokens_total = source.get("tokens_total")
    if not isinstance(tokens_input, (int, float)):
        tokens_input = source.get("prompt_eval_count") if isinstance(source.get("prompt_eval_count"), (int, float)) else None
    if not isinstance(tokens_output, (int, float)):
        tokens_output = source.get("eval_count") if isinstance(source.get("eval_count"), (int, float)) else None
    if not isinstance(tokens_total, (int, float)) and isinstance(tokens_input, (int, float)) and isinstance(tokens_output, (int, float)):
        tokens_total = tokens_input + tokens_output

    return {
        "status": source.get("status") if isinstance(source.get("status"), str) else ("error" if http_status >= 400 else "error"),
        "error_code": source.get("error_code") if isinstance(source.get("error_code"), str) else source.get("code"),
        "error_message": source.get("error_message") if isinstance(source.get("error_message"), str) else source.get("message"),
        "trace_id": source.get("trace_id") if isinstance(source.get("trace_id"), str) else None,
        "retrieval_status": source.get("retrieval_status") if isinstance(source.get("retrieval_status"), str) else None,
        "chunk_ids": source.get("chunk_ids") if isinstance(source.get("chunk_ids"), list) else [],
        "document_ids": source.get("document_ids") if isinstance(source.get("document_ids"), list) else [],
        "source_filenames": source.get("source_filenames") if isinstance(source.get("source_filenames"), list) else [],
        "latency_ms": source.get("latency_ms") if isinstance(source.get("latency_ms"), (int, float)) else 0,
        "tokens_input": tokens_input,
        "tokens_output": tokens_output,
        "tokens_total": tokens_total,
        "response_text": response_text,
        "raw_payload": payload,
    }


def comparison_value(baseline_item: dict[str, Any], case: dict[str, Any], field_name: str, default: Any = None) -> Any:
    if field_name in baseline_item:
        return baseline_item.get(field_name)
    if field_name in case:
        return case.get(field_name)
    return default


def preview_text(text: str, limit: int = 500) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[:limit]


def compare_case_result(
    *,
    case: dict[str, Any],
    baseline_item: dict[str, Any],
    actual: dict[str, Any],
) -> tuple[bool, list[dict[str, Any]]]:
    checks: list[dict[str, Any]] = []
    allowed_failure_modes = comparison_value(baseline_item, case, "allowed_failure_modes", []) or []
    actual_status = actual.get("status")
    actual_error_code = actual.get("error_code")

    status_passed = actual_status == comparison_value(baseline_item, case, "expected_status")
    if actual_status == "error" and isinstance(actual_error_code, str):
        status_passed = actual_error_code in allowed_failure_modes
    checks.append(
        {
            "name": "status",
            "passed": status_passed,
            "expected": comparison_value(baseline_item, case, "expected_status"),
            "actual": actual_status if actual_status != "error" else actual_error_code,
        }
    )

    if actual_status == "error" and status_passed:
        return True, checks

    expected_retrieval_status = comparison_value(baseline_item, case, "expected_retrieval_status")
    retrieval_passed = actual.get("retrieval_status") == expected_retrieval_status
    checks.append(
        {
            "name": "retrieval_status",
            "passed": retrieval_passed,
            "expected": expected_retrieval_status,
            "actual": actual.get("retrieval_status"),
        }
    )

    expected_source_filenames = comparison_value(baseline_item, case, "expected_source_filenames", []) or []
    actual_source_filenames = [
        item for item in actual.get("source_filenames", []) if isinstance(item, str)
    ]
    source_filenames_passed = all(
        filename in actual_source_filenames for filename in expected_source_filenames
    )
    checks.append(
        {
            "name": "source_filenames",
            "passed": source_filenames_passed,
            "expected": expected_source_filenames,
            "actual": actual_source_filenames,
        }
    )

    expected_min_chunk_count = comparison_value(baseline_item, case, "expected_min_chunk_count")
    actual_chunk_count = len(actual.get("chunk_ids", []))
    chunk_count_passed = True
    if isinstance(expected_min_chunk_count, int):
        chunk_count_passed = actual_chunk_count >= expected_min_chunk_count
    checks.append(
        {
            "name": "min_chunk_count",
            "passed": chunk_count_passed,
            "expected": expected_min_chunk_count,
            "actual": actual_chunk_count,
        }
    )

    response_text = actual.get("response_text", "")
    normalized_response_text = response_text.casefold()
    expected_answer_contains = comparison_value(baseline_item, case, "expected_answer_contains", []) or []
    expected_answer_passed = all(
        isinstance(term, str) and term.casefold() in normalized_response_text
        for term in expected_answer_contains
    )
    checks.append(
        {
            "name": "expected_answer_contains",
            "passed": expected_answer_passed,
            "expected": expected_answer_contains,
            "actual": response_text,
        }
    )

    forbidden_terms = comparison_value(baseline_item, case, "forbidden_terms", case.get("forbidden_terms", [])) or []
    forbidden_terms_passed = all(
        isinstance(term, str) and term.casefold() not in normalized_response_text
        for term in forbidden_terms
    )
    checks.append(
        {
            "name": "forbidden_terms",
            "passed": forbidden_terms_passed,
            "expected": forbidden_terms,
            "actual": response_text,
        }
    )

    return all(check["passed"] for check in checks), checks


def build_backend_error_result(case: dict[str, Any], message: str) -> dict[str, Any]:
    failures = [
        {
            "name": "backend",
            "expected": "available",
            "actual": message,
        }
    ]
    return {
        "case_id": case.get("id"),
        "input": case.get("input"),
        "passed": False,
        "status": "failed",
        "chat_status": "error",
        "error_code": "backend_unavailable",
        "error_message": message,
        "trace_id": None,
        "retrieval_status": None,
        "chunk_ids": [],
        "document_ids": [],
        "source_filenames": [],
        "latency_ms": 0,
        "tokens_input": None,
        "tokens_output": None,
        "tokens_total": None,
        "checks": [
            {
                "name": "backend",
                "passed": False,
                "expected": "available",
                "actual": message,
            }
        ],
        "failures": failures,
        "response_preview": "",
    }


def summarize_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(results)
    passed = sum(1 for result in results if result.get("passed") is True)
    errors = sum(
        1
        for result in results
        if (result.get("chat_status") or result.get("status")) == "error"
    )
    failed = total - passed
    pass_rate = 0.0 if total == 0 else round(passed / total, 4)
    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "pass_rate": pass_rate,
    }


def build_run_filename(created_at: datetime | None = None) -> str:
    timestamp = (created_at or _utc_now()).strftime("%Y%m%d_%H%M%S")
    return f"{timestamp}_chat_eval_run.json"


def build_run_payload(
    *,
    run_id: str,
    created_at: str,
    base_url: str,
    source: str,
    cases_path: str,
    baseline_path: str,
    results: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "version": RUN_VERSION,
        "run_id": run_id,
        "created_at": created_at,
        "source": source,
        "base_url": base_url,
        "cases_file": cases_path,
        "baseline_file": baseline_path,
        "cases_path": cases_path,
        "baseline_path": baseline_path,
        "summary": summarize_results(results),
        "results": results,
    }


def write_run_file(out_dir: Path, payload: dict[str, Any], *, created_at: datetime | None = None) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    output_path = out_dir / build_run_filename(created_at)
    output_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    return output_path


def _parse_created_at(value: Any) -> datetime:
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return datetime.min.replace(tzinfo=timezone.utc)
    return datetime.min.replace(tzinfo=timezone.utc)


def list_saved_eval_runs(*, out_dir_str: str | None = None) -> dict[str, Any]:
    out_dir = repo_path(out_dir_str or DEFAULT_OUT_DIR)
    items: list[dict[str, Any]] = []
    if out_dir.exists():
        for path in out_dir.glob("*_chat_eval_run.json"):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if not isinstance(payload, dict):
                continue
            if payload.get("version") != RUN_VERSION:
                continue
            summary = payload.get("summary")
            if not isinstance(summary, dict):
                continue
            try:
                run_path = str(path.relative_to(REPO_ROOT))
            except ValueError:
                run_path = str(path)
            items.append(
                {
                    "run_id": payload.get("run_id"),
                    "created_at": payload.get("created_at"),
                    "source": payload.get("source"),
                    "cases_file": payload.get("cases_file"),
                    "baseline_file": payload.get("baseline_file"),
                    "summary": summary,
                    "run_path": run_path,
                }
            )

    items.sort(key=lambda item: _parse_created_at(item.get("created_at")), reverse=True)
    total_runs = len(items)
    total_cases = sum(
        summary.get("total", 0)
        for summary in (item.get("summary") for item in items)
        if isinstance(summary, dict)
    )
    total_passed = sum(
        summary.get("passed", 0)
        for summary in (item.get("summary") for item in items)
        if isinstance(summary, dict)
    )
    total_failed = sum(
        summary.get("failed", 0)
        for summary in (item.get("summary") for item in items)
        if isinstance(summary, dict)
    )
    avg_pass_rate = (
        round(
            sum(
                float(summary.get("pass_rate", 0.0))
                for summary in (item.get("summary") for item in items)
                if isinstance(summary, dict)
            ) / total_runs,
            4,
        )
        if total_runs
        else 0.0
    )
    return {
        "status": "ok",
        "total_runs": total_runs,
        "total_cases": total_cases,
        "total_passed": total_passed,
        "total_failed": total_failed,
        "avg_pass_rate": avg_pass_rate,
        "items": items,
    }


def request_case_result(
    *,
    base_url: str,
    payload: dict[str, Any],
    timeout: int,
) -> dict[str, Any]:
    try:
        response = requests.post(
            f"{base_url.rstrip('/')}/chat",
            json=payload,
            timeout=timeout,
        )
    except requests.RequestException as exc:
        raise BackendUnavailableError(str(exc)) from exc

    try:
        response_payload = response.json()
    except ValueError as exc:
        raise BackendUnavailableError("backend_invalid_json_response") from exc

    if not isinstance(response_payload, dict):
        raise BackendUnavailableError("backend_non_object_json_response")

    return normalize_chat_result(response_payload, http_status=response.status_code)


def run_chat_evals(
    *,
    base_url: str,
    cases_path_str: str,
    baseline_path_str: str,
    out_dir_str: str,
    timeout: int,
    limit: int | None,
    source: str = "cli",
    request_case_fn: RequestCaseFn | None = None,
) -> tuple[dict[str, Any], Path, int]:
    cases_path = repo_path(cases_path_str)
    baseline_path = repo_path(baseline_path_str)
    out_dir = repo_path(out_dir_str)

    cases = load_cases(cases_path)
    baseline_items = load_baseline(baseline_path)
    validate_baseline_case_ids(cases, baseline_items)

    build_case_index(cases)
    baseline_index = build_baseline_index(baseline_items)
    selected_cases = list(cases if limit is None else cases[:limit])

    run_id = uuid.uuid4().hex
    created_at_dt = _utc_now()
    created_at = created_at_dt.isoformat()
    results: list[dict[str, Any]] = []
    exit_code = 0
    case_request = request_case_fn
    if case_request is None:
        case_request = lambda payload: request_case_result(base_url=base_url, payload=payload, timeout=timeout)

    for position, case in enumerate(selected_cases):
        case_id = case.get("id")
        if not isinstance(case_id, str):
            raise RunnerConfigError(f"case_id_invalid_at_index: {position}")

        baseline_item = baseline_index.get(case_id, {})
        payload = build_chat_payload(case)
        try:
            actual = case_request(payload)
        except BackendUnavailableError:
            message = f"Backend unavailable at {base_url}"
            results.append(build_backend_error_result(case, message))
            for pending_case in selected_cases[position + 1 :]:
                results.append(build_backend_error_result(pending_case, message))
            exit_code = 2
            break

        passed, checks = compare_case_result(case=case, baseline_item=baseline_item, actual=actual)
        if not passed and exit_code == 0:
            exit_code = 1
        failures = [
            {
                "name": check["name"],
                "expected": check.get("expected"),
                "actual": check.get("actual"),
            }
            for check in checks
            if check.get("passed") is False
        ]
        results.append(
            {
                "case_id": case_id,
                "input": case.get("input"),
                "passed": passed,
                "status": "passed" if passed else "failed",
                "chat_status": actual.get("status"),
                "error_code": actual.get("error_code"),
                "error_message": actual.get("error_message"),
                "trace_id": actual.get("trace_id"),
                "retrieval_status": actual.get("retrieval_status"),
                "chunk_ids": actual.get("chunk_ids", []),
                "document_ids": actual.get("document_ids", []),
                "source_filenames": actual.get("source_filenames", []),
                "latency_ms": actual.get("latency_ms", 0),
                "tokens_input": actual.get("tokens_input"),
                "tokens_output": actual.get("tokens_output"),
                "tokens_total": actual.get("tokens_total"),
                "checks": checks,
                "failures": failures,
                "response_preview": preview_text(actual.get("response_text", "")),
            }
        )

    run_payload = build_run_payload(
        run_id=run_id,
        created_at=created_at,
        base_url=base_url,
        source=source,
        cases_path=cases_path_str,
        baseline_path=baseline_path_str,
        results=results,
    )
    output_path = write_run_file(out_dir, run_payload, created_at=created_at_dt)
    return run_payload, output_path, exit_code


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run minimal chat evals against POST /chat.")
    parser.add_argument("--base-url", default=os.getenv("CHAT_EVAL_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--cases", default=DEFAULT_CASES_PATH)
    parser.add_argument("--baseline", default=DEFAULT_BASELINE_PATH)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR)
    parser.add_argument("--timeout", default=DEFAULT_TIMEOUT, type=int)
    parser.add_argument("--limit", default=None, type=int)
    parser.add_argument("--debug", action="store_true")
    return parser.parse_args(argv)


def print_summary(run_payload: dict[str, Any], output_path: Path) -> None:
    summary = run_payload["summary"]
    print(f"Run file: {output_path}")
    print(
        "Summary: "
        f"total={summary['total']} "
        f"passed={summary['passed']} "
        f"failed={summary['failed']} "
        f"errors={summary['errors']} "
        f"pass_rate={summary['pass_rate']:.2%}"
    )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        if args.timeout <= 0:
            raise RunnerConfigError("timeout_must_be_positive")
        if args.limit is not None and args.limit <= 0:
            raise RunnerConfigError("limit_must_be_positive")
        run_payload, output_path, exit_code = run_chat_evals(
            base_url=args.base_url,
            cases_path_str=args.cases,
            baseline_path_str=args.baseline,
            out_dir_str=args.out_dir,
            timeout=args.timeout,
            limit=args.limit,
            source="cli",
        )
    except RunnerConfigError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except Exception as exc:
        if args.debug:
            raise
        print(str(exc), file=sys.stderr)
        return 2

    if exit_code == 2:
        print(f"Backend unavailable at {args.base_url}")
    print_summary(run_payload, output_path)
    return exit_code
