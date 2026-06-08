import time
from datetime import datetime, timezone
from typing import Callable

from pydantic import ValidationError

from app.adapters import backend_client
from app.config import settings
from app.contracts import ParsedDocAiCommand, ParsedDocCommand, TelegramMessage, TraceContext
from app.llm_client import LLMClientError, generate_markdown
from app.observability import append_telegram_trace, log_event, new_trace_id
from app.schemas import CreateDocumentRequest
from app.telegram_permissions import TelegramPermissionConfigError, is_telegram_user_allowed

DOC_COMMAND = "doc.create"
DOC_USAGE_TEXT = "Uso: /doc nombre.md\\ncontenido"
DOC_AI_COMMAND = "doc_ai.create"
DOC_AI_USAGE_TEXT = "Uso: /doc_ai nombre.md\\ninstrucción para el modelo"


class DocCommandParseError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


class LLMOutputValidationError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


def build_llm_prompt(user_message: str) -> str:
    return user_message.strip()


def parse_doc_command(
    text: str,
    user_id: int | None,
    chat_id: int | None,
) -> ParsedDocCommand:
    if not isinstance(user_id, int):
        raise DocCommandParseError("user_id_required", "No se pudo identificar el usuario.")
    if not isinstance(chat_id, int):
        raise DocCommandParseError("chat_id_required", "No se pudo identificar el chat.")

    raw = text.removeprefix("/doc")
    if not raw.strip() or "\n" not in raw:
        raise DocCommandParseError("invalid_doc_usage", DOC_USAGE_TEXT)

    filename, content = raw.lstrip().split("\n", 1)

    return ParsedDocCommand(
        filename=filename.strip(),
        content=content.strip(),
        user_id=user_id,
        chat_id=chat_id,
    )


def parse_doc_ai_command(
    text: str,
    user_id: int | None,
    chat_id: int | None,
) -> ParsedDocAiCommand:
    if not isinstance(user_id, int):
        raise DocCommandParseError("user_id_required", "No se pudo identificar el usuario.")
    if not isinstance(chat_id, int):
        raise DocCommandParseError("chat_id_required", "No se pudo identificar el chat.")

    raw = text.removeprefix("/doc_ai")
    parts = raw.lstrip().split(None, 1)
    if len(parts) != 2 or not parts[0].strip() or not parts[1].strip():
        raise DocCommandParseError("invalid_doc_ai_usage", DOC_AI_USAGE_TEXT)

    return ParsedDocAiCommand(
        filename=parts[0].strip(),
        prompt=parts[1].strip(),
        user_id=user_id,
        chat_id=chat_id,
    )


def _validation_error_reason(exc: ValidationError) -> str:
    first_error = exc.errors()[0]
    ctx = first_error.get("ctx") or {}
    original_error = ctx.get("error")
    if original_error:
        return str(original_error)
    return str(first_error.get("msg", "validation_error"))


def _doc_error_reply(message: str, request_id: str) -> str:
    return f"{message} (request_id={request_id})"


def _validate_llm_markdown_output(content: str) -> str:
    if not isinstance(content, str):
        raise LLMOutputValidationError("llm_output_not_text", "La salida del LLM no es texto.")

    normalized = content.replace("\r\n", "\n").replace("\r", "\n")
    if "\x00" in normalized:
        raise LLMOutputValidationError(
            "llm_output_contains_null_byte",
            "La salida del LLM contiene bytes nulos.",
        )

    normalized = normalized.strip()
    if not normalized:
        raise LLMOutputValidationError("llm_output_empty", "La salida del LLM está vacía.")

    if len(normalized) > settings.llm_max_output_chars:
        raise LLMOutputValidationError(
            "llm_output_too_large",
            "La salida del LLM supera el tamaño máximo.",
        )

    return normalized


def _trace_context(
    *,
    trace_id: str | None,
    user_id: int | None,
    chat_id: int | None,
    trace_id_factory: Callable[[], str],
) -> TraceContext:
    return TraceContext(
        trace_id=trace_id or trace_id_factory(),
        user_id=user_id,
        chat_id=chat_id,
    )


def _message_command(text: str) -> str:
    if text.startswith("/doc_ai"):
        return "doc_ai"
    if text.startswith("/doc"):
        return "doc"
    return "chat"


def _safe_int_field(value: object) -> int | None:
    return value if isinstance(value, int) else None


def _safe_token_rate(count: int | None, duration_ns: int | None) -> float | None:
    if not isinstance(count, int) or not isinstance(duration_ns, int):
        return None
    if count <= 0 or duration_ns <= 0:
        return None
    return count / duration_ns * 1_000_000_000


def _chat_trace_metadata(result: dict | None) -> dict:
    if not isinstance(result, dict):
        return {}

    prompt_eval_count = _safe_int_field(result.get("prompt_eval_count"))
    eval_count = _safe_int_field(result.get("eval_count"))
    prompt_eval_duration = _safe_int_field(result.get("prompt_eval_duration"))
    eval_duration = _safe_int_field(result.get("eval_duration"))
    total_duration = _safe_int_field(result.get("total_duration"))
    load_duration = _safe_int_field(result.get("load_duration"))
    chunk_ids = result.get("chunk_ids")
    if not isinstance(chunk_ids, list) or not all(isinstance(item, int) for item in chunk_ids):
        chunk_ids = []
    temperature = result.get("temperature")
    if not isinstance(temperature, (int, float)):
        temperature = None
    temperature_ignored = result.get("temperature_ignored")
    if not isinstance(temperature_ignored, bool):
        temperature_ignored = None

    tokens_total = None
    if prompt_eval_count is not None and eval_count is not None:
        tokens_total = prompt_eval_count + eval_count

    return {
        "provider": result.get("provider") if isinstance(result.get("provider"), str) else None,
        "temperature": temperature,
        "temperature_ignored": temperature_ignored,
        "tokens_input": prompt_eval_count,
        "tokens_output": eval_count,
        "tokens_total": tokens_total,
        "prompt_eval_count": prompt_eval_count,
        "eval_count": eval_count,
        "prompt_eval_duration_ns": prompt_eval_duration,
        "eval_duration_ns": eval_duration,
        "total_duration_ns": total_duration,
        "load_duration_ns": load_duration,
        "prompt_tokens_per_second": _safe_token_rate(prompt_eval_count, prompt_eval_duration),
        "output_tokens_per_second": _safe_token_rate(eval_count, eval_duration),
        "retrieval_status": result.get("retrieval_status"),
        "chunk_ids": chunk_ids,
    }


def _log_doc_ai_event(
    *,
    event: str,
    trace: TraceContext,
    filename: str,
    model: str,
    status: str,
    reason: str,
    started_at: float,
    output_chars: int = 0,
) -> None:
    log_event(
        component=event.rsplit(".", 1)[0],
        event=event,
        trace_id=trace.trace_id,
        request_id=trace.trace_id,
        command=DOC_AI_COMMAND,
        user_id=trace.user_id,
        chat_id=trace.chat_id,
        filename=filename,
        model=model,
        duration_ms=int((time.perf_counter() - started_at) * 1000),
        status=status,
        reason=reason,
        output_chars=output_chars,
    )


def _log_doc_attempt(
    *,
    trace: TraceContext,
    command: str,
    filename: str,
    status: str,
    reason: str,
    started_at: float,
) -> None:
    log_event(
        component="telegram.doc",
        trace_id=trace.trace_id,
        request_id=trace.trace_id,
        command=command,
        user_id=trace.user_id,
        chat_id=trace.chat_id,
        filename=filename,
        status=status,
        reason=reason,
        duration_ms=int((time.perf_counter() - started_at) * 1000),
    )


def handle_doc_command(
    text: str,
    user_id: int | None,
    chat_id: int | None,
    *,
    trace_id: str | None = None,
    trace_id_factory: Callable[[], str] = new_trace_id,
    permission_checker: Callable[[int], bool] = is_telegram_user_allowed,
    request_model_cls=CreateDocumentRequest,
    backend_create_document_fn: Callable[[CreateDocumentRequest], dict] = backend_client.create_document,
) -> str:
    trace = _trace_context(
        trace_id=trace_id,
        user_id=user_id,
        chat_id=chat_id,
        trace_id_factory=trace_id_factory,
    )
    started_at = time.perf_counter()
    command = DOC_COMMAND
    filename = ""
    status = "error"
    reason = "unexpected_error"

    try:
        parsed = parse_doc_command(text=text, user_id=user_id, chat_id=chat_id)
        command = parsed.command
        filename = parsed.filename

        if not permission_checker(parsed.user_id):
            status = "rejected"
            reason = "telegram_user_not_allowed"
            return _doc_error_reply("No autorizado para crear documentos.", trace.trace_id)

        try:
            request = request_model_cls(
                request_id=trace.trace_id,
                filename=parsed.filename,
                content=parsed.content,
                user_id=parsed.user_id,
                chat_id=parsed.chat_id,
                overwrite=False,
            )
        except ValidationError as exc:
            status = "rejected"
            reason = _validation_error_reason(exc)
            return _doc_error_reply(f"No se pudo crear el documento: {reason}", trace.trace_id)

        data = backend_create_document_fn(request)
        status = "accepted"
        reason = "created"
        return f"Documento creado: {data['filename']} ({data['chars']} caracteres)"

    except backend_client.BackendClientError as exc:
        status = "rejected" if exc.status_code < 500 else "error"
        reason = exc.code
        return _doc_error_reply(f"No se pudo crear el documento: {reason}", trace.trace_id)
    except DocCommandParseError as exc:
        status = "rejected"
        reason = exc.code
        return _doc_error_reply(exc.message, trace.trace_id)
    except TelegramPermissionConfigError:
        status = "error"
        reason = "telegram_permission_config_invalid"
        return _doc_error_reply(
            "No se pudo comprobar autorización para crear documentos.",
            trace.trace_id,
        )
    except Exception as exc:
        reason = exc.__class__.__name__
        return _doc_error_reply("No se pudo crear el documento: unexpected_error", trace.trace_id)
    finally:
        _log_doc_attempt(
            trace=trace,
            command=command,
            filename=filename,
            status=status,
            reason=reason,
            started_at=started_at,
        )


def handle_doc_ai_command(
    text: str,
    user_id: int | None,
    chat_id: int | None,
    *,
    trace_id: str | None = None,
    trace_id_factory: Callable[[], str] = new_trace_id,
    permission_checker: Callable[[int], bool] = is_telegram_user_allowed,
    request_model_cls=CreateDocumentRequest,
    backend_create_document_fn: Callable[[CreateDocumentRequest], dict] = backend_client.create_document,
    llm_generate_fn: Callable[[str, str], str] = generate_markdown,
    model_name: str = "",
) -> str:
    trace = _trace_context(
        trace_id=trace_id,
        user_id=user_id,
        chat_id=chat_id,
        trace_id_factory=trace_id_factory,
    )
    started_at = time.perf_counter()
    filename = ""
    model = model_name or "local-model"
    status = "error"
    reason = "unexpected_error"
    output_chars = 0

    try:
        parsed = parse_doc_ai_command(text=text, user_id=user_id, chat_id=chat_id)
        filename = parsed.filename
        _log_doc_ai_event(
            event="telegram.doc_ai.received",
            trace=trace,
            filename=filename,
            model=model,
            status="received",
            reason="received",
            started_at=started_at,
        )

        if not permission_checker(parsed.user_id):
            status = "rejected"
            reason = "telegram_user_not_allowed"
            return _doc_error_reply("No autorizado para crear documentos.", trace.trace_id)

        try:
            request_model_cls(
                request_id=trace.trace_id,
                filename=parsed.filename,
                content="contenido temporal para validar filename",
                user_id=parsed.user_id,
                chat_id=parsed.chat_id,
                overwrite=False,
            )
        except ValidationError as exc:
            status = "rejected"
            reason = _validation_error_reason(exc)
            return _doc_error_reply(f"No se pudo crear el documento: {reason}", trace.trace_id)

        llm_started_at = time.perf_counter()
        _log_doc_ai_event(
            event="llm.request.started",
            trace=trace,
            filename=filename,
            model=model,
            status="started",
            reason="started",
            started_at=llm_started_at,
        )

        try:
            llm_output = llm_generate_fn(parsed.prompt, request_id=trace.trace_id)
        except LLMClientError as exc:
            _log_doc_ai_event(
                event="llm.request.failed",
                trace=trace,
                filename=filename,
                model=model,
                status="error",
                reason=exc.code,
                started_at=llm_started_at,
            )
            status = "rejected"
            reason = exc.code
            return _doc_error_reply(f"No se pudo generar el documento: {reason}", trace.trace_id)

        try:
            content = _validate_llm_markdown_output(llm_output)
        except LLMOutputValidationError as exc:
            _log_doc_ai_event(
                event="llm.request.finished",
                trace=trace,
                filename=filename,
                model=model,
                status="rejected",
                reason=exc.code,
                started_at=llm_started_at,
                output_chars=len(llm_output) if isinstance(llm_output, str) else 0,
            )
            status = "rejected"
            reason = exc.code
            return _doc_error_reply(f"No se pudo crear el documento: {reason}", trace.trace_id)

        output_chars = len(content)
        _log_doc_ai_event(
            event="llm.request.finished",
            trace=trace,
            filename=filename,
            model=model,
            status="ok",
            reason="generated",
            started_at=llm_started_at,
            output_chars=output_chars,
        )

        try:
            request = request_model_cls(
                request_id=trace.trace_id,
                filename=parsed.filename,
                content=content,
                user_id=parsed.user_id,
                chat_id=parsed.chat_id,
                overwrite=False,
            )
        except ValidationError as exc:
            status = "rejected"
            reason = _validation_error_reason(exc)
            return _doc_error_reply(f"No se pudo crear el documento: {reason}", trace.trace_id)

        data = backend_create_document_fn(request)
        status = "accepted"
        reason = "created"
        return f"Documento creado: {data['filename']} ({data['chars']} caracteres)"

    except backend_client.BackendClientError as exc:
        status = "rejected" if exc.status_code < 500 else "error"
        reason = exc.code
        return _doc_error_reply(f"No se pudo crear el documento: {reason}", trace.trace_id)
    except DocCommandParseError as exc:
        status = "rejected"
        reason = exc.code
        return _doc_error_reply(exc.message, trace.trace_id)
    except TelegramPermissionConfigError:
        status = "error"
        reason = "telegram_permission_config_invalid"
        return _doc_error_reply(
            "No se pudo comprobar autorización para crear documentos.",
            trace.trace_id,
        )
    except Exception as exc:
        reason = exc.__class__.__name__
        return _doc_error_reply("No se pudo crear el documento: unexpected_error", trace.trace_id)
    finally:
        _log_doc_ai_event(
            event="telegram.doc_ai.created" if status == "accepted" else "telegram.doc_ai.rejected",
            trace=trace,
            filename=filename,
            model=model,
            status=status,
            reason=reason,
            started_at=started_at,
            output_chars=output_chars,
        )


def handle_message(
    msg: dict,
    *,
    send_message_fn: Callable[[int, str], None],
    ask_chat_fn: Callable[[str], dict],
    doc_handler: Callable[..., str] = handle_doc_command,
    doc_ai_handler: Callable[..., str] = handle_doc_ai_command,
    trace_id_factory: Callable[[], str] = new_trace_id,
) -> None:
    started_at = time.perf_counter()
    created_at = datetime.now(timezone.utc)
    message = TelegramMessage(
        chat_id=msg["chat"]["id"],
        user_id=msg.get("from", {}).get("id"),
        text=msg.get("text", "").strip(),
    )
    trace = _trace_context(
        trace_id=None,
        user_id=message.user_id,
        chat_id=message.chat_id,
        trace_id_factory=trace_id_factory,
    )
    command = _message_command(message.text)
    response_text = ""
    model: str | None = None
    status = "error"
    error_code: str | None = None
    trace_metadata: dict = {}

    log_event(
        component="telegram.message",
        event="telegram.message.received",
        trace_id=trace.trace_id,
        chat_id=message.chat_id,
        user_id=message.user_id,
        text_chars=len(message.text),
        command=command,
    )

    try:
        if not message.text:
            response_text = "Mensaje vacío o no soportado."
            send_message_fn(message.chat_id, response_text)
            status = "ok"
            return

        if message.text.startswith("/doc_ai"):
            model = settings.effective_ollama_model()
            response = doc_ai_handler(
                message.text,
                user_id=message.user_id,
                chat_id=message.chat_id,
                trace_id=trace.trace_id,
            )
            response_text = response
            send_message_fn(message.chat_id, response)
            status = "ok"
        elif message.text.startswith("/doc"):
            response = doc_handler(
                message.text,
                user_id=message.user_id,
                chat_id=message.chat_id,
                trace_id=trace.trace_id,
            )
            response_text = response
            send_message_fn(message.chat_id, response)
            status = "ok"
        else:
            try:
                result = ask_chat_fn(
                    message.text,
                    trace_id=trace.trace_id,
                    user_id=message.user_id,
                    chat_id=message.chat_id,
                )
            except backend_client.BackendClientError as exc:
                trace_provider = getattr(exc, "provider", None)
                trace_model = getattr(exc, "model", None)
                trace_temperature = getattr(exc, "temperature", None)
                trace_temperature_ignored = getattr(exc, "temperature_ignored", None)
                if isinstance(trace_model, str) and trace_model.strip():
                    model = trace_model
                if isinstance(trace_provider, str) and trace_provider.strip():
                    trace_metadata["provider"] = trace_provider
                if isinstance(trace_temperature, (int, float)):
                    trace_metadata["temperature"] = trace_temperature
                if isinstance(trace_temperature_ignored, bool):
                    trace_metadata["temperature_ignored"] = trace_temperature_ignored
                log_event(
                    component="telegram.chat",
                    event="telegram.chat.failed",
                    trace_id=trace.trace_id,
                    chat_id=message.chat_id,
                    user_id=message.user_id,
                    status="error",
                    error_code=exc.code,
                    latency_ms=0,
                )
                error_code = exc.code
                response_text = _doc_error_reply("No se pudo procesar el mensaje.", trace.trace_id)
                send_message_fn(
                    message.chat_id,
                    response_text,
                )
                return

            answer = result.get("answer", "")
            response_text = answer
            model = result.get("model")
            status = result.get("status", "ok")
            trace_metadata = _chat_trace_metadata(result)
            log_event(
                component="telegram.chat",
                event="telegram.chat.completed",
                trace_id=trace.trace_id,
                chat_id=message.chat_id,
                user_id=message.user_id,
                model=model,
                status=status,
                latency_ms=result.get("latency_ms", 0),
            )
            send_message_fn(message.chat_id, answer)
    except Exception as exc:
        error_code = exc.__class__.__name__
        response_text = f"ERROR: {exc}"
        log_event(
            component="telegram.message",
            event="telegram.message.failed",
            trace_id=trace.trace_id,
            chat_id=message.chat_id,
            user_id=message.user_id,
            status="error",
            reason=exc.__class__.__name__,
        )
        send_message_fn(message.chat_id, response_text)
    finally:
        try:
            append_telegram_trace(
                trace_id=trace.trace_id,
                request_id=trace.trace_id,
                chat_id=message.chat_id,
                user_id=message.user_id,
                command=command,
                text_chars=len(message.text),
                response_chars=len(response_text),
                model=model,
                status=status,
                error_code=error_code,
                latency_ms=int((time.perf_counter() - started_at) * 1000),
                created_at=created_at,
                include_text=settings.telegram_trace_include_text,
                text=message.text,
                metadata=trace_metadata,
            )
        except Exception as exc:
            log_event(
                component="telegram.trace",
                event="telegram.trace.persist_failed",
                trace_id=trace.trace_id,
                chat_id=message.chat_id,
                user_id=message.user_id,
                status="error",
                reason=exc.__class__.__name__,
            )
def main_loop(
    *,
    get_updates_fn: Callable[[], list[dict]],
    handle_message_fn: Callable[[dict], None],
    sleep_seconds: int = 1,
) -> None:
    while True:
        try:
            for update in get_updates_fn():
                if "message" in update:
                    handle_message_fn(update["message"])
        except KeyboardInterrupt:
            break
        except Exception:
            pass

        time.sleep(sleep_seconds)
