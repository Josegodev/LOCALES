import secrets
import logging

from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings
from app.observability.logging import log_event

bearer_scheme = HTTPBearer(auto_error=False)


def require_dev_token(
    credentials: HTTPAuthorizationCredentials | None = None,
) -> None:
    configured_token = settings.jose_dev_token
    if not configured_token:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "code": "dev_token_not_configured",
                "message": "JOSE_DEV_TOKEN no esta configurado en el servidor.",
            },
        )

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail={
                "status": "error",
                "code": "invalid_token",
                "message": "Authorization Bearer token requerido.",
            },
        )

    if not secrets.compare_digest(credentials.credentials, configured_token):
        raise HTTPException(
            status_code=401,
            detail={
                "status": "error",
                "code": "invalid_token",
                "message": "Authorization Bearer token invalido.",
            },
        )


def require_chat_access(
    credentials: HTTPAuthorizationCredentials | None = None,
    *,
    auth_header_present: bool = False,
) -> None:
    mode = settings.chat_auth_mode
    auth_required = mode == "bearer_required"
    log_event(
        component="auth.chat",
        event="chat_auth_checked",
        route="/chat",
        auth_required=auth_required,
        auth_header_present=auth_header_present,
        chat_auth_mode=mode,
        level=logging.WARNING if mode == "local_open" else logging.INFO,
    )

    if mode == "disabled":
        raise HTTPException(
            status_code=403,
            detail={
                "status": "error",
                "code": "chat_disabled",
                "message": "/chat esta deshabilitado por configuracion.",
            },
        )

    if mode == "bearer_required":
        require_dev_token(credentials)
