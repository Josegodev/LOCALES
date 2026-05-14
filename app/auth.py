import secrets

from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings

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
