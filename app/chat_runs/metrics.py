from __future__ import annotations

from math import isfinite
from typing import Any


EVIDENCE_FOUND_STATUS = "EVIDENCE_FOUND"


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


def _normalized_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    candidate = value.strip()
    return candidate or None


def _is_ok_run(run: dict[str, Any]) -> bool:
    return _normalized_text(run.get("status")) == "ok"


def _is_error_run(run: dict[str, Any]) -> bool:
    if _is_ok_run(run):
        return False
    return True


def _rate(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return round(numerator / denominator, 4)


def _mean(values: list[Any]) -> float | None:
    numbers = [number for number in (_safe_number(value) for value in values) if number is not None]
    if not numbers:
        return None
    return round(sum(numbers) / len(numbers), 4)


def _label(run: dict[str, Any], field_name: str) -> str:
    value = _normalized_text(run.get(field_name))
    return value or "unknown"


def percentile(values: list[Any], p: int | float) -> float | None:
    numbers = sorted(number for number in (_safe_number(value) for value in values) if number is not None)
    if not numbers:
        return None
    if p <= 0:
        return numbers[0]
    if p >= 100:
        return numbers[-1]

    rank = (len(numbers) - 1) * (float(p) / 100.0)
    lower_index = int(rank)
    upper_index = min(lower_index + 1, len(numbers) - 1)
    fraction = rank - lower_index
    lower_value = numbers[lower_index]
    upper_value = numbers[upper_index]
    return round(lower_value + (upper_value - lower_value) * fraction, 4)


def _summarize_group(runs: list[dict[str, Any]]) -> dict[str, Any]:
    total_runs = len(runs)
    ok_runs = sum(1 for run in runs if _is_ok_run(run))
    error_runs = sum(1 for run in runs if _is_error_run(run))
    fallback_runs = sum(1 for run in runs if run.get("fallback_used") is True)

    rag_runs = [run for run in runs if run.get("use_rag") is True]
    rag_hits = sum(1 for run in rag_runs if _normalized_text(run.get("retrieval_status")) == EVIDENCE_FOUND_STATUS)

    return {
        "total_runs": total_runs,
        "ok_runs": ok_runs,
        "error_runs": error_runs,
        "error_rate": _rate(error_runs, total_runs),
        "avg_latency_ms": _mean([run.get("latency_ms") for run in runs]),
        "p50_latency_ms": percentile([run.get("latency_ms") for run in runs], 50),
        "p95_latency_ms": percentile([run.get("latency_ms") for run in runs], 95),
        "p99_latency_ms": percentile([run.get("latency_ms") for run in runs], 99),
        "avg_tokens_per_second": _mean([run.get("output_tokens_per_second") for run in runs]),
        "fallback_rate": _rate(fallback_runs, total_runs),
        "rag_hit_rate": _rate(rag_hits, len(rag_runs)),
    }


def group_by_model(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for run in runs:
        grouped.setdefault(_label(run, "model"), []).append(run)

    items = []
    for model_name, model_runs in grouped.items():
        summary = _summarize_group(model_runs)
        items.append({"model": model_name, **summary})

    items.sort(key=lambda item: (-item["total_runs"], item["model"].casefold()))
    return items


def group_by_provider(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for run in runs:
        grouped.setdefault(_label(run, "provider"), []).append(run)

    items = []
    for provider_name, provider_runs in grouped.items():
        summary = _summarize_group(provider_runs)
        items.append({"provider": provider_name, **summary})

    items.sort(key=lambda item: (-item["total_runs"], item["provider"].casefold()))
    return items


def summarize_runs(runs: list[dict[str, Any]]) -> dict[str, Any]:
    summary = _summarize_group(runs)
    summary["by_model"] = group_by_model(runs)
    summary["by_provider"] = group_by_provider(runs)
    return summary
