from fastapi import APIRouter, Depends, Header, Query
from fastapi.security import HTTPAuthorizationCredentials

from app.api.runtime_bridge import main_module
from app.auth import bearer_scheme, require_chat_access
from app.schemas import ChatTraceListResponse, ChatTraceResetResponse

router = APIRouter()


@router.get("/api/traces/chat", response_model=ChatTraceListResponse)
def chat_trace_runs(
    limit: int = Query(default=50, ge=1, le=200),
    _: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    authorization: str | None = Header(default=None),
) -> dict:
    require_chat_access(_, auth_header_present=authorization is not None)
    items = [record.model_dump() for record in main_module().list_chat_runs(limit=limit)]
    return {"status": "ok", "items": items, "count": len(items)}


@router.post("/api/traces/chat/reset", response_model=ChatTraceResetResponse)
def reset_chat_trace_runs(
    _: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    authorization: str | None = Header(default=None),
) -> dict:
    require_chat_access(_, auth_header_present=authorization is not None)
    app_main = main_module()
    removed_count = app_main.clear_chat_runs()
    app_main.log_event(
        component="frontend.chat.traces",
        event="chat_trace_runs_reset",
        removed_count=removed_count,
    )
    return {"status": "ok", "removed_count": removed_count}
