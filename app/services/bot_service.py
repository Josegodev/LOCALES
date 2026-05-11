import time
from datetime import datetime, timezone
from typing import Callable

from pydantic import ValidationError

from app.adapters import backend_client
from app.config import settings
from app.contracts import ParsedDocAiCommand, ParsedDocCommand, TelegramMessage, TraceContext
from app.llm_client import LLMClientError, generate_markdown
from app.observability import (
    append_telegram_trace,
    log_event,
    new_trace_id,
    write_telegram_conversation_record,
    write_telegram_eval_run,
)
from app.schemas import CreateDocumentRequest
try:
    from app.services.repo_analyzer_service import (
        build_repo_trace_metadata,
        handle_repo_command,
        is_repo_command,
    )
except ModuleNotFoundError:
    def is_repo_command(text: str) -> bool:
        return text.startswith("/repo")

    def handle_repo_command(*args, **kwargs) -> dict:
        return {
            "status": "error",
            "error_code": "repo_analyzer_unavailable",
            "error_message": "Servicio /repo no disponible en este runtime.",
            "reply_text": "Servicio /repo no disponible en este runtime.",
        }

    def build_repo_trace_metadata(result: dict) -> dict:
        return {
            "prompt_version": "telegram_repo_unavailable",
            "error_code": result.get("error_code"),
            "final_message_preview": result.get("reply_text"),
        }
from app.telegram_permissions import TelegramPermissionConfigError, is_telegram_user_allowed

DOC_COMMAND = "doc.create"
DOC_USAGE_TEXT = "Uso: /doc nombre.md\\ncontenido"
DOC_AI_COMMAND = "doc_ai.create"
DOC_AI_USAGE_TEXT = "Uso: /doc_ai nombre.md\\ninstrucción para el modelo"
NO_EVIDENCE_MARKER = "NO_EVIDENCE_FOR_ANSWER"
NO_EVIDENCE_EXPLANATION = "No hay evidencia documental suficiente para responder."
ANSWER_MODE_DOCUMENTARY = "documentary_answer"
ANSWER_MODE_SAFE_REFUSAL = "safe_refusal"
ANSWER_MODE_MODEL_INTERNAL = "model_internal_answer"
ACTIVE_CONTEXT_REASON_OVERRIDDEN = "overridden_by_explicit_intent"
ACTIVE_CONTEXT_REASON_SHORT = "short_or_ambiguous_query"
_ACTIVE_DOCUMENT_CONTEXTS: dict[int, dict[str, object]] = {}


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


def reset_active_document_contexts() -> None:
    _ACTIVE_DOCUMENT_CONTEXTS.clear()


def _message_preview(text: str, limit: int = 200) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[:limit].rstrip() + "..."


def _strip_no_evidence_markers(answer: str) -> str:
    normalized = answer.replace("\r\n", "\n").replace("\r", "\n")
    for token in (NO_EVIDENCE_MARKER, NO_EVIDENCE_EXPLANATION):
        normalized = normalized.replace(token, "")
    lines = [line.strip() for line in normalized.split("\n") if line.strip()]
    return "\n".join(lines).strip()


def _normalize_answer_mode(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    candidate = value.strip()
    return candidate or None


def _finalize_telegram_chat_message(result: dict) -> tuple[str, str]:
    retrieval_status = str(result.get("retrieval_status") or "").strip()
    answer_mode = _normalize_answer_mode(result.get("answer_mode"))
    raw_answer = result.get("answer")
    answer = raw_answer if isinstance(raw_answer, str) else ""

    if retrieval_status == "EVIDENCE_FOUND":
        cleaned = _strip_no_evidence_markers(answer)
        if cleaned:
            return cleaned, answer_mode or ANSWER_MODE_DOCUMENTARY
        return answer.strip(), answer_mode or ANSWER_MODE_DOCUMENTARY

    if retrieval_status in {"NO_EVIDENCE", "NO_EVIDENCE_FOR_ANSWER"} and answer_mode == ANSWER_MODE_MODEL_INTERNAL:
        return answer.strip(), answer_mode

    if retrieval_status in {"NO_EVIDENCE", "NO_EVIDENCE_FOR_ANSWER"}:
        return f"{NO_EVIDENCE_MARKER}\n{NO_EVIDENCE_EXPLANATION}", answer_mode or ANSWER_MODE_SAFE_REFUSAL

    return answer.strip(), answer_mode or "unknown"


def _read_active_document_context(chat_id: int | None) -> dict[str, object]:
    if not isinstance(chat_id, int):
        return {}

    stored = _ACTIVE_DOCUMENT_CONTEXTS.get(chat_id)
    if not isinstance(stored, dict):
        return {}

    return dict(stored)


def _store_active_document_context(chat_id: int | None, result: dict) -> None:
    if not isinstance(chat_id, int):
        return
    if not isinstance(result, dict):
        return
    if result.get("answer_mode") != ANSWER_MODE_DOCUMENTARY:
        return

    document_ids = result.get("document_ids")
    if not isinstance(document_ids, list) or not document_ids or not isinstance(document_ids[0], int):
        return

    selected_filenames = result.get("selected_filenames")
    source_filenames = result.get("source_filenames")
    active_document_title = None
    if isinstance(selected_filenames, list) and selected_filenames and isinstance(selected_filenames[0], str):
        active_document_title = selected_filenames[0]
    elif isinstance(source_filenames, list) and source_filenames and isinstance(source_filenames[0], str):
        active_document_title = source_filenames[0]

    _ACTIVE_DOCUMENT_CONTEXTS[chat_id] = {
        "active_document_id": document_ids[0],
        "active_document_title": active_document_title,
        "active_corpus": result.get("selected_corpus"),
        "last_source_intent": result.get("source_intent"),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


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
    if is_repo_command(text):
        return "repo"
    if text.startswith("/doc_ai"):
        return "doc_ai"
    if text.startswith("/doc"):
        return "doc"
    return "chat"


def _safe_token_rate(count: int | None, duration_ns: int | None) -> float | None:
    if not isinstance(count, int) or not isinstance(duration_ns, int):
        return None
    if count <= 0 or duration_ns <= 0:
        return None
    return count / duration_ns * 1_000_000_000


def _chat_trace_metadata(result: dict | None) -> dict:
    if not isinstance(result, dict):
        return {}

    prompt_eval_count = result.get("prompt_eval_count")
    eval_count = result.get("eval_count")
    prompt_eval_duration = result.get("prompt_eval_duration")
    eval_duration = result.get("eval_duration")
    total_duration = result.get("total_duration")
    load_duration = result.get("load_duration")
    chunk_ids = result.get("chunk_ids")
    document_ids = result.get("document_ids")

    if not isinstance(prompt_eval_count, int):
        prompt_eval_count = None
    if not isinstance(eval_count, int):
        eval_count = None
    if not isinstance(prompt_eval_duration, int):
        prompt_eval_duration = None
    if not isinstance(eval_duration, int):
        eval_duration = None
    if not isinstance(total_duration, int):
        total_duration = None
    if not isinstance(load_duration, int):
        load_duration = None
    if not isinstance(chunk_ids, list) or not all(isinstance(item, int) for item in chunk_ids):
        chunk_ids = []
    if not isinstance(document_ids, list) or not all(isinstance(item, int) for item in document_ids):
        document_ids = []
    temperature = result.get("temperature")
    if not isinstance(temperature, (int, float)):
        temperature = None
    temperature_ignored = result.get("temperature_ignored")
    if not isinstance(temperature_ignored, bool):
        temperature_ignored = None
    use_rag = result.get("use_rag")
    if not isinstance(use_rag, bool):
        use_rag = None
    warnings = result.get("warnings")
    if not isinstance(warnings, list) or not all(isinstance(item, str) for item in warnings):
        warnings = []
    generation_config = result.get("generation_config")
    if not isinstance(generation_config, dict):
        generation_config = None
    top_k = result.get("top_k")
    if not isinstance(top_k, int):
        top_k = None
    source_filenames = result.get("source_filenames")
    if not isinstance(source_filenames, list) or not all(isinstance(item, str) for item in source_filenames):
        source_filenames = []
    query_original = result.get("query_original")
    if not isinstance(query_original, str):
        query_original = None
    query_normalized = result.get("query_normalized")
    if not isinstance(query_normalized, str):
        query_normalized = None
    query_terms = result.get("query_terms")
    if not isinstance(query_terms, list) or not all(isinstance(item, str) for item in query_terms):
        query_terms = []
    quoted_terms = result.get("quoted_terms")
    if not isinstance(quoted_terms, list) or not all(isinstance(item, str) for item in quoted_terms):
        quoted_terms = []
    source_intent = result.get("source_intent")
    if not isinstance(source_intent, str):
        source_intent = None
    selected_corpus = result.get("selected_corpus")
    if not isinstance(selected_corpus, str):
        selected_corpus = None
    active_document_id = result.get("active_document_id")
    if not isinstance(active_document_id, int):
        active_document_id = None
    active_document_title = result.get("active_document_title")
    if not isinstance(active_document_title, str):
        active_document_title = None
    active_context_used = result.get("active_context_used")
    if not isinstance(active_context_used, bool):
        active_context_used = False
    active_context_reason = result.get("active_context_reason")
    if not isinstance(active_context_reason, str):
        active_context_reason = None
    evidence_used = result.get("evidence_used")
    if not isinstance(evidence_used, bool):
        evidence_used = bool(chunk_ids or document_ids or source_filenames)
    fallback_used = result.get("fallback_used")
    if not isinstance(fallback_used, bool):
        fallback_used = bool(
            _normalize_answer_mode(result.get("answer_mode")) == ANSWER_MODE_MODEL_INTERNAL
            or str(result.get("retrieval_status") or "").strip() in {"NO_EVIDENCE", "NO_EVIDENCE_FOR_ANSWER"}
        )
    query_expansion_used = result.get("query_expansion_used")
    if not isinstance(query_expansion_used, bool):
        query_expansion_used = False
    query_expansion_reason = result.get("query_expansion_reason")
    if not isinstance(query_expansion_reason, str):
        query_expansion_reason = None
    expanded_query_terms = result.get("expanded_query_terms")
    if not isinstance(expanded_query_terms, list) or not all(isinstance(item, str) for item in expanded_query_terms):
        expanded_query_terms = []
    candidate_filenames = result.get("candidate_filenames")
    if not isinstance(candidate_filenames, list) or not all(isinstance(item, str) for item in candidate_filenames):
        candidate_filenames = []
    selected_filenames = result.get("selected_filenames")
    if not isinstance(selected_filenames, list) or not all(isinstance(item, str) for item in selected_filenames):
        selected_filenames = []
    scores = result.get("scores")
    if not isinstance(scores, list) or not all(isinstance(item, int) for item in scores):
        scores = []
    answer_mode = result.get("answer_mode")
    if not isinstance(answer_mode, str):
        answer_mode = None
    final_message_preview = result.get("answer")
    if not isinstance(final_message_preview, str):
        final_message_preview = None

    tokens_total = None
    if prompt_eval_count is not None and eval_count is not None:
        tokens_total = prompt_eval_count + eval_count

    return {
        "provider": result.get("provider") if isinstance(result.get("provider"), str) else None,
        "temperature": temperature,
        "temperature_ignored": temperature_ignored,
        "generation_config": generation_config,
        "prompt_version": "telegram_rag_v1",
        "top_k": top_k,
        "query_original": query_original,
        "query_normalized": query_normalized,
        "query_terms": query_terms,
        "quoted_terms": quoted_terms,
        "source_intent": source_intent,
        "selected_corpus": selected_corpus,
        "active_document_id": active_document_id,
        "active_document_title": active_document_title,
        "active_context_used": active_context_used,
        "active_context_reason": active_context_reason,
        "evidence_used": evidence_used,
        "fallback_used": fallback_used,
        "query_expansion_used": query_expansion_used,
        "query_expansion_reason": query_expansion_reason,
        "expanded_query_terms": expanded_query_terms,
        "candidate_filenames": candidate_filenames,
        "selected_filenames": selected_filenames,
        "scores": scores,
        "answer_mode": answer_mode,
        "final_message_preview": _message_preview(final_message_preview) if final_message_preview else None,
        "source_filenames": source_filenames,
        "use_rag": use_rag,
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
        "document_ids": document_ids,
        "warnings": warnings,
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
    repo_handler: Callable[..., dict] = handle_repo_command,
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
    error_message: str | None = None
    trace_metadata: dict = {
        "prompt_version": "telegram_rag_v1",
        "top_k": None,
        "query_original": message.text,
        "retrieval_status": None,
        "active_document_id": None,
        "active_document_title": None,
        "active_context_used": False,
        "active_context_reason": None,
        "evidence_used": False,
        "fallback_used": False,
        "query_expansion_used": False,
        "query_expansion_reason": None,
        "expanded_query_terms": [],
        "chunk_ids": [],
        "document_ids": [],
        "source_filenames": [],
        "answer_mode": None,
        "final_message_preview": None,
    }

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

        if is_repo_command(message.text):
            result = repo_handler(
                message.text,
                user_id=message.user_id,
                trace_id=trace.trace_id,
            )
            response_text = result.get("reply_text", "")
            model = result.get("model")
            status = result.get("status", "error")
            error_code = result.get("error_code")
            error_message = result.get("error_message")
            trace_metadata = build_repo_trace_metadata(result)
            log_event(
                component="telegram.repo",
                event="telegram.repo.completed" if status == "ok" else "telegram.repo.failed",
                trace_id=trace.trace_id,
                chat_id=message.chat_id,
                user_id=message.user_id,
                model=model,
                status=status,
                error_code=error_code,
                latency_ms=result.get("latency_ms", 0),
                repo_path=result.get("repo_path"),
            )
            send_message_fn(message.chat_id, response_text)
        elif message.text.startswith("/doc_ai"):
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
                active_context = _read_active_document_context(message.chat_id)
                result = ask_chat_fn(
                    message.text,
                    trace_id=trace.trace_id,
                    user_id=message.user_id,
                    chat_id=message.chat_id,
                    active_document_id=active_context.get("active_document_id"),
                    active_document_title=active_context.get("active_document_title"),
                    active_corpus=active_context.get("active_corpus"),
                    last_source_intent=active_context.get("last_source_intent"),
                )
            except backend_client.BackendClientError as exc:
                trace_provider = getattr(exc, "provider", None)
                trace_model = getattr(exc, "model", None)
                trace_temperature = getattr(exc, "temperature", None)
                trace_temperature_ignored = getattr(exc, "temperature_ignored", None)
                trace_use_rag = getattr(exc, "use_rag", None)
                trace_generation_config = getattr(exc, "generation_config", None)
                trace_top_k = getattr(exc, "top_k", None)
                trace_source_filenames = getattr(exc, "source_filenames", None)
                trace_retrieval_status = getattr(exc, "retrieval_status", None)
                trace_chunk_ids = getattr(exc, "chunk_ids", None)
                trace_document_ids = getattr(exc, "document_ids", None)
                trace_query_original = getattr(exc, "query_original", None)
                if isinstance(trace_model, str) and trace_model.strip():
                    model = trace_model
                if isinstance(trace_provider, str) and trace_provider.strip():
                    trace_metadata["provider"] = trace_provider
                if isinstance(trace_temperature, (int, float)):
                    trace_metadata["temperature"] = trace_temperature
                if isinstance(trace_temperature_ignored, bool):
                    trace_metadata["temperature_ignored"] = trace_temperature_ignored
                if isinstance(trace_generation_config, dict):
                    trace_metadata["generation_config"] = trace_generation_config
                if isinstance(trace_top_k, int):
                    trace_metadata["top_k"] = trace_top_k
                if isinstance(trace_source_filenames, list) and all(isinstance(item, str) for item in trace_source_filenames):
                    trace_metadata["source_filenames"] = trace_source_filenames
                if isinstance(trace_retrieval_status, str) and trace_retrieval_status.strip():
                    trace_metadata["retrieval_status"] = trace_retrieval_status
                if isinstance(trace_chunk_ids, list) and all(isinstance(item, int) for item in trace_chunk_ids):
                    trace_metadata["chunk_ids"] = trace_chunk_ids
                if isinstance(trace_document_ids, list) and all(isinstance(item, int) for item in trace_document_ids):
                    trace_metadata["document_ids"] = trace_document_ids
                if isinstance(trace_query_original, str) and trace_query_original.strip():
                    trace_metadata["query_original"] = trace_query_original
                if isinstance(trace_use_rag, bool):
                    trace_metadata["use_rag"] = trace_use_rag
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
                error_message = exc.message
                response_text = _doc_error_reply("No se pudo procesar el mensaje.", trace.trace_id)
                send_message_fn(
                    message.chat_id,
                    response_text,
                )
                return

            answer, answer_mode = _finalize_telegram_chat_message(result)
            response_text = answer
            result["answer"] = answer
            result["answer_mode"] = answer_mode
            model = result.get("model")
            status = result.get("status", "ok")
            trace_metadata = _chat_trace_metadata(result)
            _store_active_document_context(message.chat_id, result)
            log_event(
                component="telegram.chat",
                event="telegram.chat.completed",
                trace_id=trace.trace_id,
                chat_id=message.chat_id,
                user_id=message.user_id,
                model=model,
                use_rag=result.get("use_rag"),
                status=status,
                latency_ms=result.get("latency_ms", 0),
                query_original=trace_metadata.get("query_original"),
                retrieval_status=trace_metadata.get("retrieval_status"),
                active_document_id=trace_metadata.get("active_document_id"),
                active_document_title=trace_metadata.get("active_document_title"),
                active_context_used=trace_metadata.get("active_context_used"),
                active_context_reason=trace_metadata.get("active_context_reason"),
                evidence_used=trace_metadata.get("evidence_used"),
                fallback_used=trace_metadata.get("fallback_used"),
                query_expansion_used=trace_metadata.get("query_expansion_used"),
                query_expansion_reason=trace_metadata.get("query_expansion_reason"),
                expanded_query_terms=trace_metadata.get("expanded_query_terms"),
                source_intent=trace_metadata.get("source_intent"),
                selected_corpus=trace_metadata.get("selected_corpus"),
                chunks_found=len(trace_metadata.get("chunk_ids", [])),
                chunk_ids=trace_metadata.get("chunk_ids"),
                selected_filenames=trace_metadata.get("selected_filenames"),
                answer_mode=trace_metadata.get("answer_mode"),
                final_message_preview=trace_metadata.get("final_message_preview"),
            )
            send_message_fn(message.chat_id, answer)
    except Exception as exc:
        error_code = exc.__class__.__name__
        error_message = str(exc)
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
        final_latency_ms = int((time.perf_counter() - started_at) * 1000)
        try:
            write_telegram_conversation_record(
                trace_id=trace.trace_id,
                chat_id=message.chat_id,
                user_id=message.user_id,
                command=command,
                model=model,
                input_text=message.text,
                response_text=response_text,
                status=status,
                latency_ms=final_latency_ms,
                error_code=error_code,
                error_message=error_message,
                created_at=created_at,
                metadata=trace_metadata,
            )
        except Exception as exc:
            log_event(
                component="telegram.memory",
                event="telegram.memory.persist_failed",
                trace_id=trace.trace_id,
                chat_id=message.chat_id,
                user_id=message.user_id,
                status="warning",
                reason=exc.__class__.__name__,
            )
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
                latency_ms=final_latency_ms,
                created_at=created_at,
                include_text=settings.telegram_trace_include_text,
                text=message.text,
                response_text=response_text,
                error_message=error_message,
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
        try:
            write_telegram_eval_run(
                trace_id=trace.trace_id,
                request_id=trace.trace_id,
                chat_id=message.chat_id,
                user_id=message.user_id,
                command=command,
                model=model,
                input_text=message.text,
                response_text=response_text,
                status=status,
                latency_ms=final_latency_ms,
                error_code=error_code,
                error_message=error_message,
                created_at=created_at,
                include_text=settings.telegram_trace_include_text,
                metadata=trace_metadata,
            )
        except Exception as exc:
            log_event(
                component="telegram.eval",
                event="telegram.eval.persist_failed",
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
