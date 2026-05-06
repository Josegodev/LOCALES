"""FastAPI entrypoint for the isolated LLM lab."""

from __future__ import annotations

import json
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException

from .model_adapter import ModelAdapter
from .validator import validate_answer_output, validate_proposal_output

BASE_DIR = Path(__file__).resolve().parent
RAG_DIR = BASE_DIR / "rag"
ARTIFACTS_DIR = BASE_DIR / "artifacts"
EVAL_CASES_PATH = BASE_DIR / "eval" / "eval_cases.json"

app = FastAPI(title="NUCLEO LLM Lab", version="0.1.0")
adapter = ModelAdapter()


@app.post("/rag/query")
def rag_query(payload: dict[str, Any]) -> dict[str, Any]:
    started = time.perf_counter()
    query = _required_string(payload, "query")
    top_k = _bounded_int(payload.get("top_k", 3), "top_k", minimum=1, maximum=10)

    prompt = f"local_rag_query: {query}"
    response = {"query": query, "hits": _query_local_docs(query=query, top_k=top_k)}
    latency_ms = _latency_ms(started)
    _write_trace(
        endpoint="rag_query",
        input_payload=payload,
        prompt=prompt,
        provider="rag",
        provider_endpoint="rag:local",
        model_id="rag:local",
        raw_output=response["hits"],
        validated_output=response,
        fallback_used=False,
        fallback_reason=None,
        latency_ms=latency_ms,
    )
    return response


@app.post("/model/proposal")
def model_proposal(payload: dict[str, Any]) -> dict[str, Any]:
    started = time.perf_counter()
    response, trace = _proposal_core(payload)
    _write_trace(endpoint="model_proposal", input_payload=payload, latency_ms=_latency_ms(started), **trace)
    return response


@app.post("/model/answer")
def model_answer(payload: dict[str, Any]) -> dict[str, Any]:
    started = time.perf_counter()
    response, trace = _answer_core(payload)
    _write_trace(endpoint="model_answer", input_payload=payload, latency_ms=_latency_ms(started), **trace)
    return response


@app.post("/eval/run")
def eval_run(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    started = time.perf_counter()
    payload = payload or {}
    requested_case_ids = set(payload.get("case_ids", []))
    cases = _load_eval_cases()
    if requested_case_ids:
        cases = [case for case in cases if case.get("id") in requested_case_ids]

    results = [_run_eval_case(case) for case in cases]
    passed = sum(1 for result in results if result["passed"])
    response = {
        "run_id": uuid.uuid4().hex,
        "total": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "results": results,
    }
    _write_trace(
        endpoint="eval_run",
        input_payload=payload,
        prompt="eval_run",
        provider="eval",
        provider_endpoint="eval:local",
        model_id="eval:local",
        raw_output=results,
        validated_output=response,
        fallback_used=any(result.get("fallback_used") for result in results),
        fallback_reason="case_fallback_used" if any(result.get("fallback_used") for result in results) else None,
        latency_ms=_latency_ms(started),
    )
    return response


def _proposal_core(payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    task = _required_string(payload, "task")
    context = _optional_object(payload.get("context", {}), "context")
    requested_model_id = _optional_string_or_none(payload.get("model_id"), "model_id")
    prompt = _build_prompt(kind="proposal", user_text=task, context=context)
    try:
        adapter_result = adapter.generate_proposal(
            prompt=prompt,
            model_id=requested_model_id,
            task=task,
            context=context,
        )
        provider = adapter_result.provider
        provider_endpoint = adapter_result.endpoint
        model_id = adapter_result.model_id
        raw_output = adapter_result.raw_output
    except Exception as exc:
        provider = "adapter"
        provider_endpoint = "adapter:error"
        model_id = requested_model_id or "unknown"
        raw_output = json.dumps({"adapter_error": str(exc)}, sort_keys=True)
    validation = validate_proposal_output(raw_output)
    return validation.validated_output, {
        "prompt": prompt,
        "provider": provider,
        "provider_endpoint": provider_endpoint,
        "model_id": model_id,
        "raw_output": raw_output,
        "validated_output": validation.validated_output,
        "fallback_used": validation.fallback_used,
        "fallback_reason": validation.fallback_reason,
    }


def _answer_core(payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    question = _required_string(payload, "question")
    context = _optional_object(payload.get("context", {}), "context")
    requested_model_id = _optional_string_or_none(payload.get("model_id"), "model_id")
    prompt = _build_prompt(kind="answer", user_text=question, context=context)
    try:
        adapter_result = adapter.generate_answer(
            prompt=prompt,
            model_id=requested_model_id,
            question=question,
            context=context,
        )
        provider = adapter_result.provider
        provider_endpoint = adapter_result.endpoint
        model_id = adapter_result.model_id
        raw_output = adapter_result.raw_output
    except Exception as exc:
        provider = "adapter"
        provider_endpoint = "adapter:error"
        model_id = requested_model_id or "unknown"
        raw_output = json.dumps({"adapter_error": str(exc)}, sort_keys=True)
    validation = validate_answer_output(raw_output)
    return validation.validated_output, {
        "prompt": prompt,
        "provider": provider,
        "provider_endpoint": provider_endpoint,
        "model_id": model_id,
        "raw_output": raw_output,
        "validated_output": validation.validated_output,
        "fallback_used": validation.fallback_used,
        "fallback_reason": validation.fallback_reason,
    }


def _run_eval_case(case: dict[str, Any]) -> dict[str, Any]:
    case_id = case.get("id", "unknown")
    kind = case.get("kind")
    case_input = case.get("input", {})
    expect = case.get("expect", {})

    try:
        if kind == "proposal":
            output, trace = _proposal_core(case_input)
        elif kind == "answer":
            output, trace = _answer_core(case_input)
        elif kind == "rag":
            query = _required_string(case_input, "query")
            top_k = _bounded_int(case_input.get("top_k", 3), "top_k", minimum=1, maximum=10)
            output = {"query": query, "hits": _query_local_docs(query=query, top_k=top_k)}
            trace = {
                "provider": "rag",
                "provider_endpoint": "rag:local",
                "model_id": "rag:local",
                "fallback_used": False,
                "fallback_reason": None,
            }
        else:
            raise ValueError(f"unknown eval kind: {kind}")
    except Exception as exc:
        return {
            "id": case_id,
            "kind": kind,
            "passed": False,
            "error": str(exc),
            "fallback_used": False,
            "fallback_reason": None,
        }

    checks = _check_expectations(output=output, trace=trace, expect=expect)
    return {
        "id": case_id,
        "kind": kind,
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
        "fallback_used": trace.get("fallback_used", False),
        "fallback_reason": trace.get("fallback_reason"),
        "output": output,
    }


def _check_expectations(
    *,
    output: dict[str, Any],
    trace: dict[str, Any],
    expect: dict[str, Any],
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for key, expected in expect.items():
        if key == "fallback_used":
            actual = trace.get("fallback_used")
        elif key == "fallback_reason":
            actual = trace.get("fallback_reason")
        elif key == "min_hits":
            actual = len(output.get("hits", []))
            checks.append({"field": key, "expected": expected, "actual": actual, "passed": actual >= expected})
            continue
        else:
            actual = output.get(key)
        checks.append({"field": key, "expected": expected, "actual": actual, "passed": actual == expected})
    return checks


def _query_local_docs(*, query: str, top_k: int) -> list[dict[str, Any]]:
    terms = [term for term in re.findall(r"[a-z0-9_]+", query.lower()) if len(term) > 1]
    if not terms:
        return []

    hits: list[dict[str, Any]] = []
    for path in sorted(RAG_DIR.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".md", ".txt", ".json"}:
            continue
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        score = sum(lowered.count(term) for term in terms)
        if score <= 0:
            continue
        hits.append(
            {
                "source": str(path.relative_to(BASE_DIR)),
                "score": score,
                "excerpt": _excerpt(text=text, terms=terms),
            }
        )

    return sorted(hits, key=lambda item: (-item["score"], item["source"]))[:top_k]


def _excerpt(*, text: str, terms: list[str], radius: int = 160) -> str:
    lowered = text.lower()
    indexes = [lowered.find(term) for term in terms if lowered.find(term) >= 0]
    start_at = min(indexes) if indexes else 0
    start = max(0, start_at - radius)
    end = min(len(text), start_at + radius)
    return " ".join(text[start:end].split())


def _build_prompt(*, kind: str, user_text: str, context: dict[str, Any]) -> str:
    return "\n".join(
        [
            "You are an experimental LLM lab model.",
            "Return JSON only.",
            "Never execute actions.",
            f"Task type: {kind}",
            f"Input: {user_text}",
            f"Context: {json.dumps(context, sort_keys=True)}",
        ]
    )


def _write_trace(
    *,
    endpoint: str,
    input_payload: dict[str, Any],
    prompt: str,
    provider: str,
    provider_endpoint: str,
    model_id: str,
    raw_output: Any,
    validated_output: dict[str, Any],
    fallback_used: bool,
    fallback_reason: str | None,
    latency_ms: int,
) -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    trace = {
        "request_id": uuid.uuid4().hex,
        "endpoint": endpoint,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input": input_payload,
        "prompt": prompt,
        "provider": provider,
        "provider_endpoint": provider_endpoint,
        "model_id": model_id,
        "raw_output": raw_output,
        "validated_output": validated_output,
        "fallback_used": fallback_used,
        "fallback_reason": fallback_reason,
        "latency_ms": latency_ms,
    }
    path = ARTIFACTS_DIR / f"{trace['created_at'].replace(':', '-')}_{endpoint}_{trace['request_id']}.json"
    path.write_text(json.dumps(trace, indent=2, sort_keys=True), encoding="utf-8")


def _load_eval_cases() -> list[dict[str, Any]]:
    try:
        data = json.loads(EVAL_CASES_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail="eval_cases.json not found") from exc
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail="eval_cases.json is not valid JSON") from exc

    if not isinstance(data, list):
        raise HTTPException(status_code=500, detail="eval_cases.json must contain a list")
    return data


def _required_string(payload: dict[str, Any], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise HTTPException(status_code=400, detail=f"{field} must be a non-empty string")
    return value


def _optional_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise HTTPException(status_code=400, detail=f"{field} must be a non-empty string")
    return value


def _optional_string_or_none(value: Any, field: str) -> str | None:
    if value is None:
        return None
    return _optional_string(value, field)


def _optional_object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise HTTPException(status_code=400, detail=f"{field} must be an object")
    return value


def _bounded_int(value: Any, field: str, *, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise HTTPException(status_code=400, detail=f"{field} must be an integer")
    if value < minimum or value > maximum:
        raise HTTPException(status_code=400, detail=f"{field} must be between {minimum} and {maximum}")
    return value


def _latency_ms(started: float) -> int:
    return round((time.perf_counter() - started) * 1000)
