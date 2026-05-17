from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials

from app.auth import bearer_scheme, require_chat_access
from app.chat_runs.metrics import summarize_runs
from app.chat_runs.store import get_chat_run, load_chat_runs


router = APIRouter()


def _require_access(
    credentials: HTTPAuthorizationCredentials | None,
    authorization: str | None,
) -> None:
    require_chat_access(credentials, auth_header_present=authorization is not None)


def _normalized_filter_text(value: str | None) -> str | None:
    if not isinstance(value, str):
        return None
    candidate = value.strip()
    if not candidate:
        return None
    return candidate.casefold()


def _apply_filters(
    runs: list[dict[str, Any]],
    *,
    model: str | None,
    provider: str | None,
    use_rag: bool | None,
    status: str | None,
) -> list[dict[str, Any]]:
    model_filter = _normalized_filter_text(model)
    provider_filter = _normalized_filter_text(provider)
    status_filter = _normalized_filter_text(status)

    filtered: list[dict[str, Any]] = []
    for run in runs:
        run_model = _normalized_filter_text(run.get("model"))
        run_provider = _normalized_filter_text(run.get("provider"))
        run_status = _normalized_filter_text(run.get("status"))

        if model_filter is not None and run_model != model_filter:
            continue
        if provider_filter is not None and run_provider != provider_filter:
            continue
        if use_rag is not None and run.get("use_rag") is not use_rag:
            continue
        if status_filter is not None and run_status != status_filter:
            continue
        filtered.append(run)

    return filtered


@router.get("/chat-runs")
def list_chat_runs(
    model: str | None = Query(default=None),
    provider: str | None = Query(default=None),
    use_rag: bool | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    _: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    _require_access(_, authorization)
    loaded = load_chat_runs()
    filtered = _apply_filters(
        loaded.items,
        model=model,
        provider=provider,
        use_rag=use_rag,
        status=status,
    )
    items = filtered[:limit]
    return {
        "items": items,
        "count": len(items),
        "total_filtered": len(filtered),
        "skipped_files_count": loaded.skipped_files_count,
        "runs_dir": str(loaded.runs_dir),
    }


@router.get("/chat-runs/stats")
def chat_runs_stats(
    model: str | None = Query(default=None),
    provider: str | None = Query(default=None),
    use_rag: bool | None = Query(default=None),
    status: str | None = Query(default=None),
    _: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    _require_access(_, authorization)
    loaded = load_chat_runs()
    filtered = _apply_filters(
        loaded.items,
        model=model,
        provider=provider,
        use_rag=use_rag,
        status=status,
    )
    summary = summarize_runs(filtered)
    return {
        **summary,
        "total_filtered": len(filtered),
        "skipped_files_count": loaded.skipped_files_count,
        "runs_dir": str(loaded.runs_dir),
    }


@router.get("/chat-runs/{trace_id}")
def get_chat_run_by_trace_id(
    trace_id: str,
    _: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    _require_access(_, authorization)
    run = get_chat_run(trace_id)
    if run is None:
        raise HTTPException(
            status_code=404,
            detail={
                "status": "error",
                "code": "chat_run_not_found",
                "message": f"Chat run no encontrado: {trace_id}",
            },
        )
    return run
