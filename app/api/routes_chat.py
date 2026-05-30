from fastapi import APIRouter, Depends, Header
from fastapi.security import HTTPAuthorizationCredentials

from app.api.runtime_bridge import main_module
from app.auth import bearer_scheme, require_chat_access
from app.schemas import ChatRequest, ChatResponse

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    _: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    authorization: str | None = Header(default=None),
) -> ChatResponse:
    require_chat_access(_, auth_header_present=authorization is not None)
    return main_module().run_chat_request(request)
