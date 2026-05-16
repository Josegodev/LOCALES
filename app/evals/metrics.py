from __future__ import annotations

from math import isfinite, sqrt
from typing import Any

from app.evals.schemas import (
    ModelMetrics,
    OperationalModelStats,
    OperationalModelTemperatureStats,
    RunRecord,
    TimeSeriesPoint,
)


NO_EVIDENCE_STATUS = "NO_EVIDENCE"


def _run_value(run: RunRecord | dict[str, Any], field_name: str) -> Any:
    if isinstance(run, dict):
        return run.get(field_name)
    return getattr(run, field_name, None)


def _normalized_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    candidate = value.strip()
    return candidate or None


def safe_number(value: Any) -> float | None:
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


def _derived_tokens_total(run: RunRecord | dict[str, Any]) -> float | None:
    explicit_total = safe_number(_run_value(run, "tokens_total"))
    if explicit_total is not None:
        return explicit_total

    tokens_input = safe_number(_run_value(run, "tokens_input"))
    tokens_output = safe_number(_run_value(run, "tokens_output"))
    if tokens_input is None or tokens_output is None:
        return None
    return tokens_input + tokens_output


def _tokens_per_second(run: RunRecord | dict[str, Any]) -> float | None:
    if not is_ok_run(run):
        return None

    explicit_value = safe_number(_run_value(run, "output_tokens_per_second"))
    if explicit_value is not None:
        return explicit_value

    latency_ms = safe_number(_run_value(run, "latency_ms"))
    tokens_output = safe_number(_run_value(run, "tokens_output"))
    if latency_ms is None or latency_ms <= 0 or tokens_output is None:
        return None

    return round(tokens_output / (latency_ms / 1000.0), 4)


def _numbers(values: list[int | float | None]) -> list[float]:
    return [float(value) for value in values if isinstance(value, (int, float))]


def mean(values: list[Any]) -> float | None:
    numbers = [number for number in (safe_number(value) for value in values) if number is not None]
    if not numbers:
        return None
    return round(sum(numbers) / len(numbers), 4)


def safe_mean(values: list[int | float | None]) -> float | None:
    return mean(values)


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


def stddev(values: list[Any]) -> float | None:
    numbers = [number for number in (safe_number(value) for value in values) if number is not None]
    if not numbers:
        return None
    if len(numbers) == 1:
        return 0.0
    mean_value = sum(numbers) / len(numbers)
    variance = sum((value - mean_value) ** 2 for value in numbers) / len(numbers)
    return round(sqrt(variance), 4)


def safe_std(values: list[int | float | None]) -> float | None:
    return stddev(values)


def percentile(values: list[Any], p: int | float) -> float | None:
    """Deterministic linear interpolation between adjacent ranks on a sorted sample."""
    numbers = sorted(number for number in (safe_number(value) for value in values) if number is not None)
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


def rate(matched: int, total_runs: int) -> float | None:
    if total_runs == 0:
        return None
    return round(matched / total_runs, 4)


def _rate(matched: int, total_runs: int) -> float | None:
    return rate(matched, total_runs)


def _model_label(run: RunRecord) -> str:
    return run.model or "unknown"


def _operational_model_label(run: RunRecord | dict[str, Any]) -> str:
    model = _normalized_text(_run_value(run, "model"))
    return model or "unknown"


def _operational_temperature_value(run: RunRecord | dict[str, Any]) -> float | None:
    return safe_number(_run_value(run, "temperature"))


def is_ok_run(run: RunRecord | dict[str, Any]) -> bool:
    return _normalized_text(_run_value(run, "status")) == "ok"


def is_timeout_run(run: RunRecord | dict[str, Any], timeout_ms: int = 10_000) -> bool:
    status = _normalized_text(_run_value(run, "status"))
    if status == "timeout":
        return True

    error_type = _normalized_text(_run_value(run, "error_type"))
    if error_type == "timeout":
        return True

    error_code = _normalized_text(_run_value(run, "error_code"))
    if isinstance(error_code, str) and "timeout" in error_code.casefold():
        return True

    latency_ms = safe_number(_run_value(run, "latency_ms"))
    return latency_ms is not None and latency_ms > float(timeout_ms)


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


def build_model_operational_stats(
    runs: list[RunRecord | dict[str, Any]],
    timeout_ms: int = 10_000,
) -> list[OperationalModelStats]:
    grouped: dict[str, list[RunRecord | dict[str, Any]]] = {}
    for run in runs:
        grouped.setdefault(_operational_model_label(run), []).append(run)

    return _build_grouped_operational_stats(grouped, timeout_ms=timeout_ms)


def build_model_temperature_operational_stats(
    runs: list[RunRecord | dict[str, Any]],
    timeout_ms: int = 10_000,
) -> list[OperationalModelTemperatureStats]:
    grouped: dict[tuple[str, float | None], list[RunRecord | dict[str, Any]]] = {}
    for run in runs:
        group_key = (_operational_model_label(run), _operational_temperature_value(run))
        grouped.setdefault(group_key, []).append(run)

    metrics: list[OperationalModelTemperatureStats] = []
    for (model_name, temperature), model_runs in grouped.items():
        base_metrics = _build_operational_stats_item(
            model_name=model_name,
            model_runs=model_runs,
            timeout_ms=timeout_ms,
        )
        metrics.append(
            OperationalModelTemperatureStats(
                **base_metrics.model_dump(),
                temperature=temperature,
            )
        )

    metrics.sort(
        key=lambda item: (
            item.avg_latency_ms is None,
            item.avg_latency_ms if item.avg_latency_ms is not None else 0.0,
            item.model.casefold(),
            item.temperature is None,
            item.temperature if item.temperature is not None else 0.0,
        )
    )
    return metrics


def _build_grouped_operational_stats(
    grouped: dict[str, list[RunRecord | dict[str, Any]]],
    *,
    timeout_ms: int,
) -> list[OperationalModelStats]:
    metrics = [
        _build_operational_stats_item(
            model_name=model_name,
            model_runs=model_runs,
            timeout_ms=timeout_ms,
        )
        for model_name, model_runs in grouped.items()
    ]
    metrics.sort(
        key=lambda item: (
            item.avg_latency_ms is None,
            item.avg_latency_ms if item.avg_latency_ms is not None else 0.0,
            item.model.casefold(),
        )
    )
    return metrics


def _build_operational_stats_item(
    *,
    model_name: str,
    model_runs: list[RunRecord | dict[str, Any]],
    timeout_ms: int,
) -> OperationalModelStats:
    latency_values = [safe_number(_run_value(run, "latency_ms")) for run in model_runs]
    tokens_input_values = [safe_number(_run_value(run, "tokens_input")) for run in model_runs]
    tokens_output_values = [safe_number(_run_value(run, "tokens_output")) for run in model_runs]
    tokens_total_values = [_derived_tokens_total(run) for run in model_runs]
    tokens_per_second_values = [_tokens_per_second(run) for run in model_runs]

    ok_count = 0
    error_count = 0
    timeout_count = 0
    for run in model_runs:
        if is_timeout_run(run, timeout_ms):
            timeout_count += 1
        elif is_ok_run(run):
            ok_count += 1
        else:
            error_count += 1

    return OperationalModelStats(
        model=model_name,
        runs=len(model_runs),
        samples_valid_latency=sum(1 for value in latency_values if value is not None),
        samples_valid_tokens=sum(1 for value in tokens_total_values if value is not None),
        ok_count=ok_count,
        error_count=error_count,
        timeout_count=timeout_count,
        success_rate=rate(ok_count, len(model_runs)),
        error_rate=rate(error_count, len(model_runs)),
        timeout_rate=rate(timeout_count, len(model_runs)),
        avg_latency_ms=mean(latency_values),
        p50_latency_ms=percentile(latency_values, 50),
        p90_latency_ms=percentile(latency_values, 90),
        p95_latency_ms=percentile(latency_values, 95),
        p99_latency_ms=percentile(latency_values, 99),
        min_latency_ms=safe_min(latency_values),
        max_latency_ms=safe_max(latency_values),
        std_latency_ms=stddev(latency_values),
        avg_tokens_input=mean(tokens_input_values),
        avg_tokens_output=mean(tokens_output_values),
        avg_tokens_total=mean(tokens_total_values),
        min_tokens_total=safe_min(tokens_total_values),
        max_tokens_total=safe_max(tokens_total_values),
        p50_tokens_total=percentile(tokens_total_values, 50),
        p95_tokens_total=percentile(tokens_total_values, 95),
        avg_tokens_per_second=mean(tokens_per_second_values),
        p50_tokens_per_second=percentile(tokens_per_second_values, 50),
        p95_tokens_per_second=percentile(tokens_per_second_values, 95),
    )


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
