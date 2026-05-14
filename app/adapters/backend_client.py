import requests

from app.config import BACKEND_URL, settings
from app.schemas import CreateDocumentRequest

FASTAPI_URL = BACKEND_URL


def _normalize_base_url(base_url: str | None) -> str:
    normalized = (base_url or FASTAPI_URL).strip().rstrip("/")
    return normalized or FASTAPI_URL


class BackendClientError(Exception):
    def __init__(self, code: str, message: str, status_code: int):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def _auth_headers() -> dict[str, str]:
    token = settings.jose_dev_token
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}


def _response_detail(response: requests.Response) -> dict:
    try:
        detail = response.json().get("detail", {})
    except Exception:
        return {}

    if isinstance(detail, dict):
        return detail
    return {}


def _response_error_reason(response: requests.Response) -> str:
    detail = _response_detail(response)
    if not detail:
        return response.text or "backend_error"

    return str(detail.get("code") or detail.get("message") or "backend_error")


def create_document(
    request: CreateDocumentRequest,
    *,
    requests_module=requests,
    base_url: str | None = None,
    timeout_seconds: int = 20,
) -> dict:
    normalized_base_url = _normalize_base_url(base_url)
    response = requests_module.post(
        f"{normalized_base_url}/documents",
        headers=_auth_headers(),
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
    active_document_id: int | None = None,
    active_document_title: str | None = None,
    active_corpus: str | None = None,
    last_source_intent: str | None = None,
    provider: str | None = None,
    model: str | None = None,
    max_tokens: int | None = None,
    temperature: float | None = None,
    use_rag: bool | None = None,
    top_k: int | None = None,
    requests_module=requests,
    base_url: str | None = None,
    timeout_seconds: int = 90,
) -> dict:
    normalized_base_url = _normalize_base_url(base_url)
    payload = {"message": message}
    optional_fields = {
        "trace_id": trace_id,
        "user_id": user_id,
        "chat_id": chat_id,
        "active_document_id": active_document_id,
        "active_document_title": active_document_title,
        "active_corpus": active_corpus,
        "last_source_intent": last_source_intent,
        "provider": provider,
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
        f"{normalized_base_url}/chat",
        headers=_auth_headers(),
        json=payload,
        timeout=timeout_seconds,
    )

    if response.status_code >= 400:
        error = BackendClientError(
            code=_response_error_reason(response),
            message="backend_chat_error",
            status_code=response.status_code,
        )
        error.provider = provider
        error.model = model
        error.temperature = temperature
        error.use_rag = use_rag
        error.top_k = top_k
        detail = _response_detail(response)
        for field_name in (
            "trace_id",
            "status",
            "retrieval_status",
            "chunk_ids",
            "document_ids",
            "source_filenames",
            "query_original",
            "use_rag",
            "provider",
            "model",
            "temperature",
            "temperature_ignored",
            "top_k",
        ):
            if field_name in detail:
                setattr(error, field_name, detail[field_name])
        raise error

    try:
        return response.json()
    except ValueError as exc:
        raise BackendClientError(
            code="backend_invalid_response",
            message="backend_invalid_response",
            status_code=502,
        ) from exc
