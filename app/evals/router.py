from fastapi import APIRouter, Depends, Header, Query
from fastapi.security import HTTPAuthorizationCredentials

from app.auth import bearer_scheme, require_chat_access
from app.config import settings
from app.evals.loader import load_runs
from app.evals.metrics import (
    build_model_operational_stats,
    build_model_temperature_operational_stats,
    build_timeseries,
    compute_by_model,
    compute_summary,
)
from app.evals.schemas import (
    MetricsSummaryResponse,
    ModelMetrics,
    OperationalStatsResponse,
    RunsByModelResponse,
    RunsListResponse,
    TimeSeriesResponse,
)


router = APIRouter()


def _require_access(
    credentials: HTTPAuthorizationCredentials | None,
    authorization: str | None,
) -> None:
    require_chat_access(credentials, auth_header_present=authorization is not None)


@router.get("/runs", response_model=RunsListResponse)
def list_runs(
    limit: int = Query(default=100, ge=1, le=1000),
    _: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    authorization: str | None = Header(default=None),
) -> RunsListResponse:
    _require_access(_, authorization)
    loaded_runs = load_runs(limit=limit)
    return RunsListResponse(
        count=len(loaded_runs.items),
        items=loaded_runs.items,
        corrupt_files_count=len(loaded_runs.corrupt_files),
        skipped_files_count=len(loaded_runs.skipped_files),
        runs_dir=str(loaded_runs.runs_dir),
    )


@router.get("/runs/summary", response_model=MetricsSummaryResponse)
def runs_summary(
    _: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    authorization: str | None = Header(default=None),
) -> MetricsSummaryResponse:
    _require_access(_, authorization)
    loaded_runs = load_runs()
    summary = compute_summary(loaded_runs.items)
    return MetricsSummaryResponse(
        total_runs=int(summary["total_runs"]),
        ok_runs=int(summary["ok_runs"]),
        failed_runs=int(summary["failed_runs"]),
        error_rate=summary["error_rate"],
        avg_latency_ms=summary["avg_latency_ms"],
        avg_tokens_total=summary["avg_tokens_total"],
        models_count=int(summary["models_count"]),
        models=summary["models"],
        corrupt_files_count=len(loaded_runs.corrupt_files),
        skipped_files_count=len(loaded_runs.skipped_files),
        runs_dir=str(loaded_runs.runs_dir),
    )


@router.get("/runs/timeseries", response_model=TimeSeriesResponse)
def runs_timeseries(
    _: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    authorization: str | None = Header(default=None),
) -> TimeSeriesResponse:
    _require_access(_, authorization)
    loaded_runs = load_runs()
    points = build_timeseries(loaded_runs.items)
    return TimeSeriesResponse(
        count=len(points),
        items=points,
        corrupt_files_count=len(loaded_runs.corrupt_files),
        skipped_files_count=len(loaded_runs.skipped_files),
        runs_dir=str(loaded_runs.runs_dir),
    )


@router.get("/runs/operational-stats", response_model=OperationalStatsResponse)
def runs_operational_stats(
    _: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    authorization: str | None = Header(default=None),
) -> OperationalStatsResponse:
    _require_access(_, authorization)
    loaded_runs = load_runs()
    by_model = build_model_operational_stats(
        loaded_runs.items,
        timeout_ms=settings.operation_timeout_ms,
    )
    by_model_temperature = build_model_temperature_operational_stats(
        loaded_runs.items,
        timeout_ms=settings.operation_timeout_ms,
    )
    by_model_temperature_included_runs = sum(item.runs for item in by_model_temperature)
    return OperationalStatsResponse(
        timeout_ms=settings.operation_timeout_ms,
        models=by_model,
        by_model=by_model,
        by_model_temperature=by_model_temperature,
        by_model_temperature_included_runs=by_model_temperature_included_runs,
        by_model_temperature_skipped_runs=max(0, len(loaded_runs.items) - by_model_temperature_included_runs),
        corrupt_files_count=len(loaded_runs.corrupt_files),
        skipped_files_count=len(loaded_runs.skipped_files),
        runs_dir=str(loaded_runs.runs_dir),
    )


@router.get("/runs/by-model/{model_name}", response_model=RunsByModelResponse)
def runs_by_model(
    model_name: str,
    _: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    authorization: str | None = Header(default=None),
) -> RunsByModelResponse:
    _require_access(_, authorization)
    loaded_runs = load_runs()
    filtered_runs = [run for run in loaded_runs.items if run.model == model_name]
    model_metrics = compute_by_model(filtered_runs)
    metrics = model_metrics[0] if model_metrics else ModelMetrics(
        model=model_name,
        runs=0,
        ok_runs=0,
        failed_runs=0,
    )
    return RunsByModelResponse(
        model=model_name,
        count=len(filtered_runs),
        items=filtered_runs,
        metrics=metrics,
        corrupt_files_count=len(loaded_runs.corrupt_files),
        skipped_files_count=len(loaded_runs.skipped_files),
        runs_dir=str(loaded_runs.runs_dir),
    )
