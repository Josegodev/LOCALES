from fastapi import APIRouter, Depends, Header, Query
from fastapi.security import HTTPAuthorizationCredentials

from app.api.runtime_bridge import main_module
from app.auth import bearer_scheme, require_chat_access
from app.schemas import ChatRunListResponse

router = APIRouter()


@router.get("/api/chat/runs", response_model=ChatRunListResponse)
def chat_runs(
    limit: int = Query(default=50, ge=1, le=200),
    _: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    authorization: str | None = Header(default=None),
) -> dict:
    require_chat_access(_, auth_header_present=authorization is not None)
    items = [record.model_dump() for record in main_module().list_chat_runs(limit=limit)]
    return {"status": "ok", "items": items, "count": len(items)}
