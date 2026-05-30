from fastapi import APIRouter, Response

router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/")
def root() -> dict:
    return {
        "service": "nucleochat",
        "status": "ok",
        "docs": "/docs",
        "health": "/health",
    }


@router.get("/favicon.ico", status_code=204)
def favicon() -> Response:
    return Response(status_code=204)
