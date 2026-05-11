import threading
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import requests

from app.adapters import backend_client, telegram_api
from app.config import settings
from app.llm_client import generate_markdown
from app.observability import log_event
from app.schemas import CreateDocumentRequest
from app.services import bot_service
from app.telegram_permissions import is_telegram_user_allowed

DEFAULT_PROVIDER = "ollama"
DEFAULT_TOP_K = 3


@dataclass
class TelegramRuntimeConfig:
    model: str
    temperature: float
    use_rag: bool


class TelegramRuntime:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._last_update_id: int | None = None
        self._started_at: str | None = None
        self._last_error: dict[str, Any] | None = None
        self._config = TelegramRuntimeConfig(
            model=settings.telegram_default_model,
            temperature=settings.telegram_default_temperature,
            use_rag=settings.telegram_default_rag_enabled,
        )

    def token_configured(self) -> bool:
        return bool(settings.telegram_bot_token)

    def config(self) -> dict[str, Any]:
        with self._lock:
            runtime_config = TelegramRuntimeConfig(
                model=self._config.model,
                temperature=self._config.temperature,
                use_rag=self._config.use_rag,
            )

        return {
            "status": "ok",
            "telegram_enabled_env": settings.telegram_enabled,
            "token_configured": self.token_configured(),
            "default_provider": DEFAULT_PROVIDER,
            "default_model": runtime_config.model,
            "default_temperature": runtime_config.temperature,
            "default_rag_enabled": runtime_config.use_rag,
        }

    def update_config(
        self,
        *,
        default_model: str | None = None,
        default_temperature: float | None = None,
        default_rag_enabled: bool | None = None,
    ) -> dict[str, Any]:
        with self._lock:
            if default_model is not None:
                normalized_model = default_model.strip()
                if normalized_model:
                    self._config.model = normalized_model
            if default_temperature is not None:
                self._config.temperature = float(default_temperature)
            if default_rag_enabled is not None:
                self._config.use_rag = bool(default_rag_enabled)

        return self.config()

    def status(self) -> dict[str, Any]:
        with self._lock:
            running = self._thread is not None and self._thread.is_alive()
            return {
                "status": "ok",
                "running": running,
                "started_at": self._started_at,
                "token_configured": self.token_configured(),
                "last_update_id": self._last_update_id,
                "last_error": self._last_error,
                "config": {
                    "default_provider": DEFAULT_PROVIDER,
                    "default_model": self._config.model,
                    "default_temperature": self._config.temperature,
                    "default_rag_enabled": self._config.use_rag,
                },
            }

    def start(self) -> dict[str, Any]:
        if not self.token_configured():
            return {
                "status": "error",
                "code": "telegram_token_missing",
                "message": "TELEGRAM_BOT_TOKEN no definido.",
            }

        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                running = True
            else:
                running = False

        if running:
            return self.status()

        with self._lock:
            self._stop_event.clear()
            self._last_error = None
            self._started_at = datetime.now(timezone.utc).isoformat()
            self._thread = threading.Thread(
                target=self._run_polling,
                name="locales-telegram-polling",
                daemon=True,
            )
            self._thread.start()

        log_event(
            component="telegram.embedded",
            event="telegram.embedded.started",
            status="started",
            provider=DEFAULT_PROVIDER,
            model=self._config.model,
            temperature=self._config.temperature,
            use_rag=self._config.use_rag,
        )
        return self.status()

    def stop(self) -> dict[str, Any]:
        with self._lock:
            thread = self._thread
            self._stop_event.set()

        if thread is not None and thread.is_alive():
            thread.join(timeout=20)

        with self._lock:
            if self._thread is not None and not self._thread.is_alive():
                self._thread = None
                self._started_at = None

        log_event(
            component="telegram.embedded",
            event="telegram.embedded.stopped",
            status="stopped",
        )
        return self.status()

    def start_if_enabled(self) -> None:
        if settings.telegram_enabled:
            self.start()

    def _runtime_config(self) -> TelegramRuntimeConfig:
        with self._lock:
            return TelegramRuntimeConfig(
                model=self._config.model,
                temperature=self._config.temperature,
                use_rag=self._config.use_rag,
            )

    def _record_error(self, code: str, message: str, **extra: Any) -> None:
        payload = {
            "code": code,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        payload.update(extra)
        with self._lock:
            self._last_error = payload

    def _get_updates(self) -> list[dict]:
        return telegram_api.get_updates(
            last_update_id=self._last_update_id,
            requests_module=requests,
            bot_token=settings.telegram_bot_token,
        )

    def _send_message(self, chat_id: int, text: str) -> None:
        telegram_api.send_message(
            chat_id,
            text,
            requests_module=requests,
            bot_token=settings.telegram_bot_token,
        )

    def _create_document_via_backend(self, request: CreateDocumentRequest) -> dict:
        return backend_client.create_document(
            request,
            requests_module=requests,
            base_url=settings.backend_base_url(),
        )

    def _handle_doc_command(self, text: str, user_id: int | None, chat_id: int | None, *, trace_id: str | None = None) -> str:
        return bot_service.handle_doc_command(
            text=text,
            user_id=user_id,
            chat_id=chat_id,
            trace_id=trace_id,
            trace_id_factory=lambda: uuid.uuid4().hex,
            permission_checker=is_telegram_user_allowed,
            request_model_cls=CreateDocumentRequest,
            backend_create_document_fn=self._create_document_via_backend,
        )

    def _handle_doc_ai_command(self, text: str, user_id: int | None, chat_id: int | None, *, trace_id: str | None = None) -> str:
        return bot_service.handle_doc_ai_command(
            text=text,
            user_id=user_id,
            chat_id=chat_id,
            trace_id=trace_id,
            trace_id_factory=lambda: uuid.uuid4().hex,
            permission_checker=is_telegram_user_allowed,
            request_model_cls=CreateDocumentRequest,
            backend_create_document_fn=self._create_document_via_backend,
            llm_generate_fn=generate_markdown,
            model_name=settings.effective_ollama_model(),
        )

    def _ask_backend(
        self,
        message: str,
        *,
        trace_id: str | None = None,
        user_id: int | None = None,
        chat_id: int | None = None,
        active_document_id: int | None = None,
        active_document_title: str | None = None,
        active_corpus: str | None = None,
        last_source_intent: str | None = None,
    ) -> dict:
        runtime_config = self._runtime_config()
        return backend_client.ask_chat(
            message,
            trace_id=trace_id,
            user_id=user_id,
            chat_id=chat_id,
            active_document_id=active_document_id,
            active_document_title=active_document_title,
            active_corpus=active_corpus,
            last_source_intent=last_source_intent,
            model=runtime_config.model,
            temperature=runtime_config.temperature,
            use_rag=runtime_config.use_rag,
            top_k=DEFAULT_TOP_K,
            requests_module=requests,
            base_url=settings.backend_base_url(),
            timeout_seconds=90,
        )

    def _handle_message(self, msg: dict) -> None:
        bot_service.handle_message(
            msg,
            send_message_fn=self._send_message,
            ask_chat_fn=self._ask_backend,
            doc_handler=self._handle_doc_command,
            doc_ai_handler=self._handle_doc_ai_command,
            trace_id_factory=lambda: uuid.uuid4().hex,
        )

    def _run_polling(self) -> None:
        consecutive_failures = 0
        while not self._stop_event.is_set():
            sleep_seconds = 1
            try:
                for update in self._get_updates():
                    self._last_update_id = update["update_id"]
                    if "message" in update:
                        self._handle_message(update["message"])
                consecutive_failures = 0
            except requests.exceptions.HTTPError as exc:
                consecutive_failures += 1
                error_info = telegram_api.classify_telegram_http_error(exc, endpoint="getUpdates")
                sleep_seconds = self._polling_backoff_seconds(
                    consecutive_failures,
                    retry_after=error_info["retry_after"],
                )
                self._record_error(error_info["code"], error_info["message"], endpoint=error_info["endpoint"])
                log_event(
                    component="telegram.embedded",
                    event="telegram.embedded.polling_failed",
                    status="error",
                    error_code=error_info["code"],
                    reason=error_info["reason"],
                    endpoint=error_info["endpoint"],
                    backoff_seconds=sleep_seconds,
                    consecutive_failures=consecutive_failures,
                )
            except requests.exceptions.RequestException as exc:
                consecutive_failures += 1
                error_info = telegram_api.classify_telegram_request_error(exc, endpoint="getUpdates")
                sleep_seconds = self._polling_backoff_seconds(consecutive_failures)
                self._record_error(error_info["code"], error_info["message"], endpoint=error_info["endpoint"])
                log_event(
                    component="telegram.embedded",
                    event="telegram.embedded.polling_failed",
                    status="error",
                    error_code=error_info["code"],
                    reason=error_info["reason"],
                    endpoint=error_info["endpoint"],
                    backoff_seconds=sleep_seconds,
                    consecutive_failures=consecutive_failures,
                )
            except telegram_api.TelegramApiError as exc:
                consecutive_failures += 1
                sleep_seconds = self._polling_backoff_seconds(consecutive_failures, retry_after=exc.retry_after)
                self._record_error(exc.code, exc.message, endpoint=exc.endpoint or "getUpdates")
                log_event(
                    component="telegram.embedded",
                    event="telegram.embedded.polling_failed",
                    status="error",
                    error_code=exc.code,
                    reason=exc.code,
                    endpoint=exc.endpoint or "getUpdates",
                    backoff_seconds=sleep_seconds,
                    consecutive_failures=consecutive_failures,
                )
            except Exception as exc:
                consecutive_failures += 1
                sleep_seconds = self._polling_backoff_seconds(consecutive_failures)
                self._record_error(exc.__class__.__name__, "Error no esperado en polling Telegram.")
                log_event(
                    component="telegram.embedded",
                    event="telegram.embedded.polling_failed",
                    status="error",
                    reason=exc.__class__.__name__,
                    backoff_seconds=sleep_seconds,
                    consecutive_failures=consecutive_failures,
                )

            self._stop_event.wait(sleep_seconds)

    @staticmethod
    def _polling_backoff_seconds(consecutive_failures: int, *, retry_after: int | None = None) -> int:
        backoff_seconds = min(30, max(1, 2 ** max(consecutive_failures - 1, 0)))
        if retry_after is not None:
            return max(backoff_seconds, retry_after)
        return backoff_seconds


telegram_runtime = TelegramRuntime()
