from __future__ import annotations

from math import sqrt

from app.evals.schemas import ModelMetrics, RunRecord, TimeSeriesPoint


NO_EVIDENCE_STATUS = "NO_EVIDENCE"


def _numbers(values: list[int | float | None]) -> list[float]:
    return [float(value) for value in values if isinstance(value, (int, float))]


def safe_mean(values: list[int | float | None]) -> float | None:
    numbers = _numbers(values)
    if not numbers:
        return None
    return round(sum(numbers) / len(numbers), 4)


def safe_min(values: list[int | float | None]) -> float | None:
    numbers = _numbers(values)
    if not numbers:
        return None
    return min(numbers)


def safe_max(values: list[int | float | None]) -> float | None:
    numbers = _numbers(values)
    if not numbers:
        return None
    return max(numbers)


def safe_std(values: list[int | float | None]) -> float | None:
    numbers = _numbers(values)
    if not numbers:
        return None
    if len(numbers) == 1:
        return 0.0
    mean_value = sum(numbers) / len(numbers)
    variance = sum((value - mean_value) ** 2 for value in numbers) / len(numbers)
    return round(sqrt(variance), 4)


def percentile(values: list[int | float | None], p: int | float) -> float | None:
    numbers = sorted(_numbers(values))
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
    interpolated = lower_value + (upper_value - lower_value) * fraction
    return round(interpolated, 4)


def _failed_run(run: RunRecord) -> bool:
    if run.error_code is not None:
        return True
    return run.status != "ok"


def _error_rate(failed_runs: int, total_runs: int) -> float | None:
    if total_runs == 0:
        return None
    return round(failed_runs / total_runs, 4)


def _rate(matched: int, total_runs: int) -> float | None:
    if total_runs == 0:
        return None
    return round(matched / total_runs, 4)


def _model_label(run: RunRecord) -> str:
    return run.model or "unknown"


def _build_model_metrics(model_name: str, runs: list[RunRecord]) -> ModelMetrics:
    total_runs = len(runs)
    failed_runs = sum(1 for run in runs if _failed_run(run))
    ok_runs = total_runs - failed_runs
    fallback_runs = sum(1 for run in runs if run.fallback_used is True)
    no_evidence_runs = sum(1 for run in runs if run.retrieval_status == NO_EVIDENCE_STATUS)

    return ModelMetrics(
        model=model_name,
        runs=total_runs,
        ok_runs=ok_runs,
        failed_runs=failed_runs,
        error_rate=_error_rate(failed_runs, total_runs),
        avg_latency_ms=safe_mean([run.latency_ms for run in runs]),
        p50_latency_ms=percentile([run.latency_ms for run in runs], 50),
        p95_latency_ms=percentile([run.latency_ms for run in runs], 95),
        max_latency_ms=safe_max([run.latency_ms for run in runs]),
        min_latency_ms=safe_min([run.latency_ms for run in runs]),
        std_latency_ms=safe_std([run.latency_ms for run in runs]),
        avg_tokens_input=safe_mean([run.tokens_input for run in runs]),
        avg_tokens_output=safe_mean([run.tokens_output for run in runs]),
        avg_tokens_total=safe_mean([run.tokens_total for run in runs]),
        avg_tokens_per_second=safe_mean([run.output_tokens_per_second for run in runs]),
        fallback_rate=_rate(fallback_runs, total_runs),
        no_evidence_rate=_rate(no_evidence_runs, total_runs),
    )


def compute_by_model(runs: list[RunRecord]) -> list[ModelMetrics]:
    grouped: dict[str, list[RunRecord]] = {}
    for run in runs:
        grouped.setdefault(_model_label(run), []).append(run)

    metrics = [
        _build_model_metrics(model_name, model_runs)
        for model_name, model_runs in grouped.items()
    ]
    metrics.sort(key=lambda item: (-item.runs, item.model.casefold()))
    return metrics


def compute_summary(runs: list[RunRecord]) -> dict[str, int | float | list[ModelMetrics] | None]:
    total_runs = len(runs)
    failed_runs = sum(1 for run in runs if _failed_run(run))
    ok_runs = total_runs - failed_runs
    models = compute_by_model(runs)

    return {
        "total_runs": total_runs,
        "ok_runs": ok_runs,
        "failed_runs": failed_runs,
        "error_rate": _error_rate(failed_runs, total_runs),
        "avg_latency_ms": safe_mean([run.latency_ms for run in runs]),
        "avg_tokens_total": safe_mean([run.tokens_total for run in runs]),
        "models_count": len(models),
        "models": models,
    }


def build_timeseries(runs: list[RunRecord]) -> list[TimeSeriesPoint]:
    points = [
        TimeSeriesPoint(
            created_at=run.created_at,
            model=run.model,
            latency_ms=run.latency_ms,
            tokens_input=run.tokens_input,
            tokens_output=run.tokens_output,
            tokens_total=run.tokens_total,
            output_tokens_per_second=run.output_tokens_per_second,
            status=run.status,
            retrieval_status=run.retrieval_status,
            fallback_used=run.fallback_used,
            trace_id=run.trace_id,
        )
        for run in runs
    ]
    points.sort(key=lambda item: item.created_at or "")
    return points
