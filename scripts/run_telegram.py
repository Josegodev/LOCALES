import sys
import time
import uuid
import math
from pathlib import Path

import requests

# Allows `python scripts/run_telegram.py` to import top-level packages (e.g. `app`).
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.adapters import backend_client, telegram_api
from app.config import settings
from app.llm_client import LLMClientError, generate_markdown
from app.observability import log_event
from app.schemas import CreateDocumentRequest
from app.services import bot_service
from app.telegram_permissions import is_telegram_user_allowed

FASTAPI_URL = backend_client.FASTAPI_URL
DEFAULT_PROVIDER = "ollama"
DEFAULT_MODEL = "granite4.1:8b"
DEFAULT_TEMPERATURE = 0.2
MODEL_ALIASES: dict[str, tuple[str, str]] = {
    "granite": ("ollama", "granite4.1:8b"),
    "mistral": ("ollama", "mistral:latest"),
    "qwen": ("ollama", "qwen2.5-coder:7b"),
    "llama": ("ollama", "llama3.1:8b"),
    "gpt": ("openai", "gpt-5.5"),
}

TG_TOKEN = settings.telegram_bot_token
if not TG_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN no definido en .env")

last_update_id = None
SELECTED_PROVIDER = DEFAULT_PROVIDER
SELECTED_MODEL = DEFAULT_MODEL
SELECTED_TEMPERATURE = DEFAULT_TEMPERATURE

DOC_COMMAND = bot_service.DOC_COMMAND
DOC_USAGE_TEXT = bot_service.DOC_USAGE_TEXT
DOC_AI_COMMAND = bot_service.DOC_AI_COMMAND
DOC_AI_USAGE_TEXT = bot_service.DOC_AI_USAGE_TEXT
DocCommandParseError = bot_service.DocCommandParseError
LLMOutputValidationError = bot_service.LLMOutputValidationError
LLMClientError = LLMClientError


def select_model() -> tuple[str, str]:
    try:
        alias = input("Insert Modelo: ").strip().lower()
    except EOFError:
        alias = ""

    if alias in MODEL_ALIASES:
        return MODEL_ALIASES[alias]

    print(
        f"Aviso: modelo invalido '{alias}'. Usando provider={DEFAULT_PROVIDER}, model={DEFAULT_MODEL}.",
        file=sys.stderr,
    )
    return DEFAULT_PROVIDER, DEFAULT_MODEL


def select_temperature() -> float:
    try:
        raw_value = input("Insert Temperature (0.0 - 1.0): ").strip()
    except EOFError:
        raw_value = ""

    try:
        temperature = float(raw_value)
    except ValueError:
        print(
            f"Aviso: temperature invalida '{raw_value}'. Usando temperature={DEFAULT_TEMPERATURE}.",
            file=sys.stderr,
        )
        return DEFAULT_TEMPERATURE

    if not math.isfinite(temperature) or temperature < 0.0 or temperature > 1.0:
        print(
            f"Aviso: temperature invalida '{raw_value}'. Usando temperature={DEFAULT_TEMPERATURE}.",
            file=sys.stderr,
        )
        return DEFAULT_TEMPERATURE

    return temperature


def parse_doc_command(text: str, user_id: int | None, chat_id: int | None):
    return bot_service.parse_doc_command(text=text, user_id=user_id, chat_id=chat_id)


def parse_doc_ai_command(text: str, user_id: int | None, chat_id: int | None):
    return bot_service.parse_doc_ai_command(text=text, user_id=user_id, chat_id=chat_id)


def _create_document_via_fastapi(request: CreateDocumentRequest) -> dict:
    return backend_client.create_document(
        request,
        requests_module=requests,
        base_url=FASTAPI_URL,
    )


def handle_doc_command(
    text: str,
    user_id: int | None,
    chat_id: int | None,
    *,
    trace_id: str | None = None,
) -> str:
    return bot_service.handle_doc_command(
        text=text,
        user_id=user_id,
        chat_id=chat_id,
        trace_id=trace_id,
        trace_id_factory=lambda: uuid.uuid4().hex,
        permission_checker=is_telegram_user_allowed,
        request_model_cls=CreateDocumentRequest,
        backend_create_document_fn=_create_document_via_fastapi,
    )


def handle_doc_ai_command(
    text: str,
    user_id: int | None,
    chat_id: int | None,
    *,
    trace_id: str | None = None,
) -> str:
    return bot_service.handle_doc_ai_command(
        text=text,
        user_id=user_id,
        chat_id=chat_id,
        trace_id=trace_id,
        trace_id_factory=lambda: uuid.uuid4().hex,
        permission_checker=is_telegram_user_allowed,
        request_model_cls=CreateDocumentRequest,
        backend_create_document_fn=_create_document_via_fastapi,
        llm_generate_fn=generate_markdown,
        model_name=settings.effective_ollama_model(),
    )


def _chat_response_error_reason(response: requests.Response) -> str:
    try:
        detail = response.json().get("detail", {})
    except Exception:
        return response.text or "backend_error"

    if isinstance(detail, dict):
        return str(detail.get("code") or detail.get("message") or "backend_error")
    return str(detail or "backend_error")


def get_updates() -> list[dict]:
    return telegram_api.get_updates(
        last_update_id=last_update_id,
        requests_module=requests,
        bot_token=TG_TOKEN,
    )


def send_message(chat_id: int, text: str) -> None:
    telegram_api.send_message(
        chat_id,
        text,
        requests_module=requests,
        bot_token=TG_TOKEN,
    )


def _polling_backoff_seconds(
    consecutive_failures: int,
    *,
    retry_after: int | None = None,
) -> int:
    backoff_seconds = min(30, max(1, 2 ** max(consecutive_failures - 1, 0)))
    if retry_after is not None:
        return max(backoff_seconds, retry_after)
    return backoff_seconds


def _telegram_endpoint_from_exception(exc: Exception) -> str:
    response = getattr(exc, "response", None)
    url = getattr(response, "url", None)

    if not isinstance(url, str):
        request = getattr(exc, "request", None)
        url = getattr(request, "url", None)

    if isinstance(url, str):
        if url.endswith("/sendMessage"):
            return "sendMessage"
        if url.endswith("/getUpdates"):
            return "getUpdates"

    return "getUpdates"


def ask_fastapi(
    message: str,
    *,
    trace_id: str | None = None,
    user_id: int | None = None,
    chat_id: int | None = None,
) -> dict:
    payload = {
        "message": message,
        "provider": SELECTED_PROVIDER,
        "model": SELECTED_MODEL,
        "temperature": SELECTED_TEMPERATURE,
    }
    optional_fields = {
        "trace_id": trace_id,
        "user_id": user_id,
        "chat_id": chat_id,
    }
    for key, value in optional_fields.items():
        if value is not None:
            payload[key] = value

    response = requests.post(
        f"{FASTAPI_URL}/chat",
        json=payload,
        timeout=90,
    )

    if response.status_code >= 400:
        error = backend_client.BackendClientError(
            code=_chat_response_error_reason(response),
            message="backend_chat_error",
            status_code=response.status_code,
        )
        error.provider = SELECTED_PROVIDER
        error.model = SELECTED_MODEL
        error.temperature = SELECTED_TEMPERATURE
        raise error

    try:
        data = response.json()
    except ValueError as exc:
        error = backend_client.BackendClientError(
            code="backend_invalid_response",
            message="backend_invalid_response",
            status_code=502,
        )
        error.provider = SELECTED_PROVIDER
        error.model = SELECTED_MODEL
        error.temperature = SELECTED_TEMPERATURE
        raise error from exc

    if not isinstance(data.get("provider"), str) or not data["provider"].strip():
        data["provider"] = SELECTED_PROVIDER
    if not isinstance(data.get("temperature"), (int, float)):
        data["temperature"] = SELECTED_TEMPERATURE

    return data


def ask_backend(text: str) -> str:
    data = ask_fastapi(text)
    return data.get("answer", str(data))


def handle_message(msg: dict) -> None:
    bot_service.handle_message(
        msg,
        send_message_fn=send_message,
        ask_chat_fn=ask_fastapi,
        doc_handler=handle_doc_command,
        doc_ai_handler=handle_doc_ai_command,
        trace_id_factory=lambda: uuid.uuid4().hex,
    )


def main() -> None:
    global last_update_id
    global SELECTED_PROVIDER
    global SELECTED_MODEL
    global SELECTED_TEMPERATURE
    consecutive_failures = 0
    SELECTED_PROVIDER, SELECTED_MODEL = select_model()
    SELECTED_TEMPERATURE = select_temperature()

    print(f"Provider seleccionado: {SELECTED_PROVIDER}")
    print(f"Modelo seleccionado: {SELECTED_MODEL}")
    print(f"Temperature seleccionada: {SELECTED_TEMPERATURE}")

    log_event(
        component="telegram.polling",
        event="telegram.polling.started",
        status="started",
        fastapi_url=f"{FASTAPI_URL}/chat",
        selected_provider=SELECTED_PROVIDER,
        selected_model=SELECTED_MODEL,
        selected_temperature=SELECTED_TEMPERATURE,
        provider=SELECTED_PROVIDER,
        model=SELECTED_MODEL,
        temperature=SELECTED_TEMPERATURE,
    )

    while True:
        sleep_seconds = 1
        try:
            for update in get_updates():
                last_update_id = update["update_id"]

                if "message" in update:
                    handle_message(update["message"])
            consecutive_failures = 0
        except KeyboardInterrupt:
            log_event(
                component="telegram.polling",
                event="telegram.polling.stopped",
                status="stopped",
                reason="keyboard_interrupt",
            )
            break
        except requests.exceptions.HTTPError as exc:
            consecutive_failures += 1
            error_info = telegram_api.classify_telegram_http_error(
                exc,
                endpoint=_telegram_endpoint_from_exception(exc),
            )
            sleep_seconds = _polling_backoff_seconds(
                consecutive_failures,
                retry_after=error_info["retry_after"],
            )
            log_event(
                component="telegram.polling",
                event="telegram.polling.failed",
                status="error",
                error_code=error_info["code"],
                reason=error_info["reason"],
                message=error_info["message"],
                endpoint=error_info["endpoint"],
                status_code=error_info["status_code"],
                response_body=error_info["response_body"],
                url=error_info["url"],
                retry_after=error_info["retry_after"],
                backoff_seconds=sleep_seconds,
                consecutive_failures=consecutive_failures,
            )
        except requests.exceptions.RequestException as exc:
            consecutive_failures += 1
            error_info = telegram_api.classify_telegram_request_error(
                exc,
                endpoint=_telegram_endpoint_from_exception(exc),
            )
            sleep_seconds = _polling_backoff_seconds(consecutive_failures)
            log_event(
                component="telegram.polling",
                event="telegram.polling.failed",
                status="error",
                error_code=error_info["code"],
                reason=error_info["reason"],
                message=error_info["message"],
                endpoint=error_info["endpoint"],
                status_code=error_info["status_code"],
                response_body=error_info["response_body"],
                url=error_info["url"],
                retry_after=error_info["retry_after"],
                backoff_seconds=sleep_seconds,
                consecutive_failures=consecutive_failures,
            )
        except telegram_api.TelegramApiError as exc:
            consecutive_failures += 1
            sleep_seconds = _polling_backoff_seconds(
                consecutive_failures,
                retry_after=exc.retry_after,
            )
            log_event(
                component="telegram.polling",
                event="telegram.polling.failed",
                status="error",
                error_code=exc.code,
                reason=exc.code,
                message=exc.message,
                endpoint=exc.endpoint or "getUpdates",
                status_code=exc.status_code,
                response_body=exc.response_body,
                url=exc.url,
                retry_after=exc.retry_after,
                backoff_seconds=sleep_seconds,
                consecutive_failures=consecutive_failures,
            )
        except Exception as exc:
            consecutive_failures += 1
            sleep_seconds = _polling_backoff_seconds(consecutive_failures)
            log_event(
                component="telegram.polling",
                event="telegram.polling.failed",
                status="error",
                reason=exc.__class__.__name__,
                backoff_seconds=sleep_seconds,
                consecutive_failures=consecutive_failures,
            )

        time.sleep(sleep_seconds)


if __name__ == "__main__":
    main()
