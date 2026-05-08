import requests

from app.schemas import CreateDocumentRequest

FASTAPI_URL = "http://127.0.0.1:8000"


class BackendClientError(Exception):
    def __init__(self, code: str, message: str, status_code: int):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def _response_error_reason(response: requests.Response) -> str:
    try:
        detail = response.json().get("detail", {})
    except Exception:
        return response.text or "backend_error"

    if isinstance(detail, dict):
        return str(detail.get("code") or detail.get("message") or "backend_error")
    return str(detail or "backend_error")


def create_document(
    request: CreateDocumentRequest,
    *,
    requests_module=requests,
    base_url: str = FASTAPI_URL,
    timeout_seconds: int = 20,
) -> dict:
    response = requests_module.post(
        f"{base_url}/documents",
        json=request.model_dump(),
        timeout=timeout_seconds,
    )

    if response.status_code >= 400:
        raise BackendClientError(
            code=_response_error_reason(response),
            message="backend_documents_error",
            status_code=response.status_code,
        )

    try:
        return response.json()
    except ValueError as exc:
        raise BackendClientError(
            code="backend_invalid_response",
            message="backend_invalid_response",
            status_code=502,
        ) from exc


def ask_chat(
    message: str,
    *,
    trace_id: str | None = None,
    user_id: int | None = None,
    chat_id: int | None = None,
    model: str | None = None,
    max_tokens: int | None = None,
    temperature: float | None = None,
    use_rag: bool | None = None,
    top_k: int | None = None,
    requests_module=requests,
    base_url: str = FASTAPI_URL,
    timeout_seconds: int = 90,
) -> dict:
    payload = {"message": message}
    optional_fields = {
        "trace_id": trace_id,
        "user_id": user_id,
        "chat_id": chat_id,
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "use_rag": use_rag,
        "top_k": top_k,
    }
    for key, value in optional_fields.items():
        if value is not None:
            payload[key] = value

    response = requests_module.post(
        f"{base_url}/chat",
        json=payload,
        timeout=timeout_seconds,
    )

    if response.status_code >= 400:
        raise BackendClientError(
            code=_response_error_reason(response),
            message="backend_chat_error",
            status_code=response.status_code,
        )

    try:
        return response.json()
    except ValueError as exc:
        raise BackendClientError(
            code="backend_invalid_response",
            message="backend_invalid_response",
            status_code=502,
        ) from exc
