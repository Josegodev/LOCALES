import sys
import time
import uuid
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

TG_TOKEN = settings.telegram_bot_token
if not TG_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN no definido en .env")

last_update_id = None

DOC_COMMAND = bot_service.DOC_COMMAND
DOC_USAGE_TEXT = bot_service.DOC_USAGE_TEXT
DOC_AI_COMMAND = bot_service.DOC_AI_COMMAND
DOC_AI_USAGE_TEXT = bot_service.DOC_AI_USAGE_TEXT
DocCommandParseError = bot_service.DocCommandParseError
LLMOutputValidationError = bot_service.LLMOutputValidationError
LLMClientError = LLMClientError


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
    return backend_client.ask_chat(
        message,
        trace_id=trace_id,
        user_id=user_id,
        chat_id=chat_id,
        requests_module=requests,
        base_url=FASTAPI_URL,
    )


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
    consecutive_failures = 0

    log_event(
        component="telegram.polling",
        event="telegram.polling.started",
        status="started",
        fastapi_url=f"{FASTAPI_URL}/chat",
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
