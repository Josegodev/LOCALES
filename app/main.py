import re
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from DB.chunks.document_context import build_document_prompt, detect_source_intent, normalize_terms
from app.config import settings
from app.rag_client import query_remote_rag
from app.observability import new_trace_id
from app.observability import log_event
from app.llm_client import LLMClientError, ask_chat, resolve_provider_model
from app.schemas import ChatRequest, ChatResponse
from app.schemas import CreateDocumentRequest, DocumentCreateResponse
from app.schemas import TelegramConfigUpdateRequest
from app.document_writer import create_document, DocumentWriteError
from app.telegram_permissions import TelegramPermissionConfigError, is_telegram_user_allowed
from app.telegram_runtime import telegram_runtime

NO_EVIDENCE_MARKER = "NO_EVIDENCE_FOR_ANSWER"
NO_EVIDENCE_EXPLANATION = "No hay evidencia documental suficiente para responder."
ANSWER_MODE_DOCUMENTARY = "documentary_answer"
ANSWER_MODE_SAFE_REFUSAL = "safe_refusal"
ANSWER_MODE_MODEL_INTERNAL = "model_internal_answer"
ANSWER_MODE_STANDARD = "standard_answer"
MARKER_ONLY_RETRIEVAL_STATUSES = {"NO_EVIDENCE", "NO_EVIDENCE_FOR_ANSWER"}
MODEL_INTERNAL_WARNING = "Respuesta generada sin evidencia documental local. Puede requerir verificación."
ACTIVE_CONTEXT_NO_EVIDENCE_WARNING = (
    "Contexto activo detectado, pero sin chunks documentales suficientes. "
    "Respuesta generada con conocimiento general del modelo."
)
MODEL_INTERNAL_VISIBLE_PREFIX = (
    "No he encontrado evidencia suficiente en los documentos cargados. "
    "Respuesta basada en conocimiento general del modelo:"
)
COMMON_QUERY_TERMS = {
    "about",
    "cosa",
    "dice",
    "does",
    "dónde",
    "donde",
    "evidencia",
    "existe",
    "mean",
    "meaning",
    "paper",
    "qué",
    "que",
    "say",
    "significa",
    "sobre",
    "thing",
    "what",
    "busca",
}


app = FastAPI(title="Local LLM Gateway")

FRONTEND_DEV_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://192.168.1.20:3000",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_DEV_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


def _no_evidence_answer() -> str:
    return f"{NO_EVIDENCE_MARKER}\n{NO_EVIDENCE_EXPLANATION}"


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


def _is_marker_only_no_evidence_answer(answer: str | None) -> bool:
    if not isinstance(answer, str):
        return False

    normalized = answer.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        return False

    if NO_EVIDENCE_MARKER not in normalized and NO_EVIDENCE_EXPLANATION not in normalized:
        return False

    return not _strip_no_evidence_markers(normalized)


def _normalize_no_evidence_retrieval_status(value: str) -> str:
    if value in MARKER_ONLY_RETRIEVAL_STATUSES:
        return NO_EVIDENCE_MARKER
    return value


def _clear_evidence_trace(context: dict) -> None:
    for key in (
        "chunks",
        "chunk_ids",
        "document_ids",
        "source_filenames",
        "selected_filenames",
        "candidate_filenames",
        "scores",
    ):
        context[key] = []


def _build_model_internal_prompt(query: str) -> str:
    return (
        "No hay evidencia documental local suficiente para responder a la pregunta siguiente.\n"
        "Responde usando solo conocimiento general del modelo.\n"
        "- No cites documentos cargados.\n"
        "- No inventes fuentes ni referencias documentales.\n"
        "- Si no estás seguro, dilo claramente.\n"
        "- Responde en el mismo idioma que la pregunta.\n\n"
        f"PREGUNTA:\n{query}"
    )


def _finalize_model_internal_answer(raw_answer: str | None) -> str:
    cleaned = _strip_no_evidence_markers(raw_answer if isinstance(raw_answer, str) else "")
    if not cleaned:
        raise LLMClientError(
            "rag_answer_contract_invalid",
            "model_internal_answer_empty_after_sanitization",
        )
    return f"{MODEL_INTERNAL_VISIBLE_PREFIX}\n{cleaned}"


def _build_model_internal_chat_response(
    *,
    result: dict,
    context: dict,
    provider: str,
    model: str,
    temperature: float,
    temperature_ignored: bool,
    use_rag: bool,
    retrieval_status: str,
) -> ChatResponse:
    response_payload = dict(result)
    response_payload.pop("retrieval_status", None)
    response_payload.pop("chunks", None)
    response_payload.pop("chunk_ids", None)
    response_payload.pop("document_ids", None)
    response_payload.pop("source_filenames", None)
    response_payload.pop("warnings", None)
    if not isinstance(response_payload.get("provider"), str) or not response_payload["provider"].strip():
        response_payload["provider"] = provider
    if not isinstance(response_payload.get("temperature"), (int, float)):
        response_payload["temperature"] = temperature
    if not isinstance(response_payload.get("temperature_ignored"), bool):
        response_payload["temperature_ignored"] = temperature_ignored
    response_payload["use_rag"] = use_rag
    response_payload["answer"] = _finalize_model_internal_answer(response_payload.get("answer"))
    warnings = list(context.get("warnings", [])) or [MODEL_INTERNAL_WARNING]
    response_payload["warnings"] = warnings
    _clear_evidence_trace(context)

    return ChatResponse(
        **response_payload,
        retrieval_status=NO_EVIDENCE_MARKER,
        answer_mode=ANSWER_MODE_MODEL_INTERNAL,
        query_original=context.get("query_original"),
        query_normalized=context.get("query_normalized"),
        query_terms=context.get("query_terms", []),
        quoted_terms=context.get("quoted_terms", []),
        source_intent=context.get("source_intent"),
        selected_corpus=context.get("selected_corpus"),
        active_document_id=context.get("active_document_id"),
        active_document_title=context.get("active_document_title"),
        active_context_used=bool(context.get("active_context_used")),
        active_context_reason=context.get("active_context_reason"),
        evidence_used=False,
        fallback_used=True,
        query_expansion_used=bool(context.get("query_expansion_used")),
        query_expansion_reason=context.get("query_expansion_reason"),
        expanded_query_terms=context.get("expanded_query_terms", []),
        candidate_filenames=[],
        selected_filenames=[],
        chunks=[],
        chunk_ids=[],
        document_ids=[],
        source_filenames=[],
        scores=[],
    )


def _evidence_used_from_payload(
    *,
    chunk_ids: list[int] | None,
    document_ids: list[int] | None,
    source_filenames: list[str] | None,
) -> bool:
    return bool(chunk_ids or document_ids or source_filenames)


def _fallback_used_from_state(
    *,
    retrieval_status: str | None,
    answer_mode: str | None,
    evidence_used: bool,
) -> bool:
    if answer_mode == ANSWER_MODE_MODEL_INTERNAL:
        return True
    if retrieval_status in MARKER_ONLY_RETRIEVAL_STATUSES:
        return True
    return not evidence_used and answer_mode == ANSWER_MODE_SAFE_REFUSAL


def _no_evidence_warning_for_context(context: dict) -> str:
    if bool(context.get("active_context_used")):
        return ACTIVE_CONTEXT_NO_EVIDENCE_WARNING
    return MODEL_INTERNAL_WARNING


def _finalize_rag_answer(
    *,
    retrieval_status: str,
    raw_answer: str | None,
) -> tuple[str, str]:
    if retrieval_status in MARKER_ONLY_RETRIEVAL_STATUSES:
        return _no_evidence_answer(), ANSWER_MODE_SAFE_REFUSAL

    candidate = raw_answer if isinstance(raw_answer, str) else ""

    if retrieval_status != "EVIDENCE_FOUND":
        cleaned = candidate.strip()
        if not cleaned:
            raise LLMClientError(
                "rag_answer_contract_invalid",
                "standard_answer_empty",
            )
        return cleaned, ANSWER_MODE_STANDARD

    cleaned = _strip_no_evidence_markers(candidate)

    if not cleaned:
        raise LLMClientError(
            "rag_answer_contract_invalid",
            "documentary_answer_empty_after_sanitization",
        )

    return cleaned, ANSWER_MODE_DOCUMENTARY


def _extract_anchor_terms(query: str) -> list[str]:
    terms = re.findall(r"[\w:-]+", query.casefold())
    anchor_terms: list[str] = []

    for term in terms:
        if term in COMMON_QUERY_TERMS:
            continue

        has_explicit_anchor_shape = (
            len(term) >= 8
            and (any(character.isdigit() for character in term) or "_" in term or "-" in term)
        )
        has_rare_alpha_shape = (
            len(term) >= 6
            and term.isalpha()
            and sum(1 for character in term if character in {"j", "k", "q", "w", "x", "y", "z"}) >= 2
        )

        if (has_explicit_anchor_shape or has_rare_alpha_shape) and term not in anchor_terms:
            anchor_terms.append(term)

    return anchor_terms


def _should_force_no_evidence(query: str, chunks: list[dict]) -> bool:
    anchor_terms = _extract_anchor_terms(query)
    if not anchor_terms:
        return False

    chunk_texts = [
        str(chunk.get("text", "")).lower()
        for chunk in chunks
        if isinstance(chunk, dict)
    ]

    return not all(
        any(anchor_term in chunk_text for chunk_text in chunk_texts)
        for anchor_term in anchor_terms
    )


def _normalize_active_document_title(value: object) -> str | None:
    if not isinstance(value, str):
        return None

    candidate = Path(value.strip()).name
    return candidate or None


def _should_use_active_context(
    *,
    query: str,
    active_document_id: int | None,
    active_document_title: str | None,
) -> tuple[bool, str | None]:
    if active_document_id is None and not active_document_title:
        return False, None

    source_intent = detect_source_intent(query)
    if source_intent != "mixed":
        return False, "overridden_by_explicit_intent"

    query_terms = normalize_terms(query)
    query_word_count = len(query.strip().split())
    is_short_or_ambiguous = len(query_terms) <= 2 or query_word_count <= 4
    if is_short_or_ambiguous:
        return True, "short_or_ambiguous_query"

    return False, "query_specific_enough"


def _normalize_source_filename(value: object) -> str | None:
    if not isinstance(value, str):
        return None

    candidate = value.strip()
    if not candidate:
        return None

    return Path(candidate).name


def _extract_chunk_source_filename(chunk: dict) -> str | None:
    for key in ("filename", "source_filename", "document_name", "source_path"):
        filename = _normalize_source_filename(chunk.get(key))
        if filename:
            return filename

    metadata = chunk.get("metadata")
    if isinstance(metadata, dict):
        for key in ("filename", "source_filename", "document_name", "source_path"):
            filename = _normalize_source_filename(metadata.get(key))
            if filename:
                return filename

    return None


def _extract_chunk_response_data(chunks: list[dict]) -> tuple[list[str], list[int], list[int], list[str]]:
    chunk_texts: list[str] = []
    chunk_ids: list[int] = []
    document_ids: list[int] = []
    seen_document_ids: set[int] = set()
    source_filenames: set[str] = set()

    for chunk in chunks:
        if not isinstance(chunk, dict):
            continue

        chunk_text = chunk.get("text")
        if isinstance(chunk_text, str) and chunk_text.strip():
            chunk_texts.append(chunk_text)

        chunk_id = chunk.get("id")
        if isinstance(chunk_id, int):
            chunk_ids.append(chunk_id)
        elif isinstance(chunk_id, str) and chunk_id.isdigit():
            chunk_ids.append(int(chunk_id))

        document_id = chunk.get("document_id")
        if isinstance(document_id, int) and document_id not in seen_document_ids:
            document_ids.append(document_id)
            seen_document_ids.add(document_id)
        elif isinstance(document_id, str) and document_id.isdigit():
            normalized_document_id = int(document_id)
            if normalized_document_id not in seen_document_ids:
                document_ids.append(normalized_document_id)
                seen_document_ids.add(normalized_document_id)

        source_filename = _extract_chunk_source_filename(chunk)
        if source_filename:
            source_filenames.add(source_filename)

    return chunk_texts, chunk_ids, document_ids, sorted(source_filenames)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.on_event("startup")
def start_embedded_telegram_if_enabled() -> None:
    telegram_runtime.start_if_enabled()


@app.on_event("shutdown")
def stop_embedded_telegram_on_shutdown() -> None:
    telegram_runtime.stop()


@app.get("/telegram/status")
def telegram_status() -> dict:
    return telegram_runtime.status()


@app.get("/telegram/config")
def telegram_config() -> dict:
    return telegram_runtime.config()


@app.post("/telegram/config")
def telegram_update_config(request: TelegramConfigUpdateRequest) -> dict:
    return telegram_runtime.update_config(
        model=request.model,
        temperature=request.temperature,
        rag_enabled=request.rag_enabled,
    )


@app.post("/telegram/start")
def telegram_start() -> dict:
    return telegram_runtime.start()


@app.post("/telegram/stop")
def telegram_stop() -> dict:
    return telegram_runtime.stop()


@app.post("/documents", response_model=DocumentCreateResponse)
def create_document_endpoint(request: CreateDocumentRequest) -> DocumentCreateResponse:
    started_at = time.perf_counter()
    status = "error"
    reason = "unexpected_error"

    try:
        if not is_telegram_user_allowed(request.user_id):
            status = "rejected"
            reason = "telegram_user_not_allowed"
            raise HTTPException(
                status_code=403,
                detail={
                    "request_id": request.request_id,
                    "status": "error",
                    "code": "telegram_user_not_allowed",
                    "message": "usuario Telegram no autorizado",
                },
            )

        result = create_document(
            filename=request.filename,
            content=request.content,
            request_id=request.request_id,
            overwrite=False,
        )
        status = "created"
        reason = "created"
        return DocumentCreateResponse(**result)
    except TelegramPermissionConfigError as exc:
        status = "error"
        reason = "telegram_permission_config_invalid"
        raise HTTPException(
            status_code=500,
            detail={
                "request_id": request.request_id,
                "status": "error",
                "code": "telegram_permission_config_invalid",
                "message": str(exc),
            },
        )
    except DocumentWriteError as exc:
        status = "rejected"
        reason = exc.code
        raise HTTPException(
            status_code=400,
            detail={
                "request_id": request.request_id,
                "status": "error",
                "code": exc.code,
                "message": exc.detail,
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        status = "error"
        reason = "document_write_internal_error"
        raise HTTPException(
            status_code=500,
            detail={
                "request_id": request.request_id,
                "status": "error",
                "code": "document_write_internal_error",
                "message": str(e),
            },
        )
    finally:
        log_event(
            component="fastapi.documents",
            trace_id=request.request_id,
            request_id=request.request_id,
            command="doc.create",
            user_id=request.user_id,
            chat_id=request.chat_id,
            filename=request.filename,
            status=status,
            reason=reason,
            duration_ms=int((time.perf_counter() - started_at) * 1000),
        )

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    trace_id = request.trace_id or new_trace_id()
    started_at = time.perf_counter()
    status = "error"
    error_code: str | None = None
    retrieval_status = "unknown"
    provider = (request.provider or "ollama").strip().lower()
    model = request.model or ""
    temperature = request.temperature
    temperature_ignored = False
    use_rag = request.use_rag
    answer_mode = "unknown"
    final_answer = ""
    warnings: list[str] = []
    context = {
        "status": "DISABLED" if not use_rag else "unknown",
        "retrieval_status": "DISABLED" if not use_rag else "unknown",
        "prompt": request.message,
        "query_original": request.message,
        "query_normalized": request.message.strip().casefold(),
        "query_terms": [],
        "quoted_terms": [],
        "source_intent": "mixed",
        "selected_corpus": "mixed",
        "active_document_id": None,
        "active_document_title": None,
        "active_context_used": False,
        "active_context_reason": None,
        "candidate_filenames": [],
        "selected_filenames": [],
        "chunks": [],
        "chunk_ids": [],
        "document_ids": [],
        "source_filenames": [],
        "scores": [],
        "warnings": [],
    }

    log_event(
        component="fastapi.chat.request",
        event="main_chat_request_received",
        trace_id=trace_id,
        endpoint="/chat",
        provider=provider,
        model=request.model,
        rag_enabled=use_rag,
        message_length=len(request.message),
    )

    try:
        provider, model = resolve_provider_model(provider, request.model)
        active_document_title = _normalize_active_document_title(request.active_document_title)
        use_active_context, active_context_reason = _should_use_active_context(
            query=request.message,
            active_document_id=request.active_document_id,
            active_document_title=active_document_title,
        )
        if use_rag:
            top_k = request.top_k or 3
            if settings.use_remote_rag:
                context = query_remote_rag(
                    query=request.message,
                    top_k=top_k,
                    trace_id=trace_id,
                    allowed_source_filenames=request.allowed_source_filenames,
                )
            else:
                rag_kwargs = {
                    "limit": top_k,
                    "allowed_source_filenames": request.allowed_source_filenames,
                }
                if request.active_document_id is not None or active_document_title is not None:
                    rag_kwargs.update(
                        active_document_id=request.active_document_id if use_active_context else None,
                        active_document_title=active_document_title if use_active_context else None,
                        allow_active_document_fallback=use_active_context,
                        active_context_reason=active_context_reason,
                    )
                context = build_document_prompt(
                    request.message,
                    **rag_kwargs,
                )
            context.setdefault("status", context.get("retrieval_status", "unknown"))
            context.setdefault("prompt", request.message)
            context.setdefault("chunks", [])
            context.setdefault("warnings", [])
            context["active_document_id"] = request.active_document_id
            context["active_document_title"] = active_document_title
            context["active_context_used"] = bool(context.get("active_context_used"))
            context["active_context_reason"] = active_context_reason
            retrieval_status = _normalize_no_evidence_retrieval_status(str(context["status"]))
            context["retrieval_status"] = retrieval_status
            if context["status"] == "EVIDENCE_FOUND" and _should_force_no_evidence(
                request.message,
                context.get("chunks", []),
            ):
                retrieval_status = NO_EVIDENCE_MARKER
                context["retrieval_status"] = retrieval_status
        else:
            retrieval_status = "DISABLED"
            context["retrieval_status"] = retrieval_status

        llm_started_at = time.perf_counter()
        llm_message = context["prompt"]
        llm_use_rag = use_rag
        if use_rag and retrieval_status in MARKER_ONLY_RETRIEVAL_STATUSES:
            llm_message = _build_model_internal_prompt(request.message)
        result = ask_chat(
            message=llm_message,
            provider=provider,
            model=model,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            use_rag=llm_use_rag,
        )
        result["latency_ms"] = int((time.perf_counter() - llm_started_at) * 1000)
        response_provider = result.get("provider")
        if isinstance(response_provider, str) and response_provider.strip():
            provider = response_provider.strip().lower()
        model = result["model"]
        if isinstance(result.get("temperature"), (int, float)):
            temperature = float(result["temperature"])
        if isinstance(result.get("temperature_ignored"), bool):
            temperature_ignored = result["temperature_ignored"]
        if isinstance(result.get("use_rag"), bool):
            use_rag = result["use_rag"]
        status = "ok"

        if use_rag and retrieval_status in MARKER_ONLY_RETRIEVAL_STATUSES:
            warnings = [_no_evidence_warning_for_context(context)]
            context["warnings"] = warnings
            internal_response = _build_model_internal_chat_response(
                result=result,
                context=context,
                provider=provider,
                model=model,
                temperature=temperature,
                temperature_ignored=temperature_ignored,
                use_rag=True,
                retrieval_status=retrieval_status,
            )
            final_answer = internal_response.answer
            answer_mode = internal_response.answer_mode or ANSWER_MODE_MODEL_INTERNAL
            return internal_response

        chunk_texts, chunk_ids, document_ids, source_filenames = _extract_chunk_response_data(context.get("chunks", [])) if use_rag else ([], [], [], [])
        response_payload = dict(result)
        response_payload.pop("retrieval_status", None)
        response_payload.pop("chunks", None)
        response_payload.pop("chunk_ids", None)
        response_payload.pop("document_ids", None)
        response_payload.pop("source_filenames", None)
        if not isinstance(response_payload.get("provider"), str) or not response_payload["provider"].strip():
            response_payload["provider"] = provider
        if not isinstance(response_payload.get("temperature"), (int, float)):
            response_payload["temperature"] = temperature
        if not isinstance(response_payload.get("temperature_ignored"), bool):
            response_payload["temperature_ignored"] = temperature_ignored
        if not isinstance(response_payload.get("use_rag"), bool):
            response_payload["use_rag"] = use_rag
        if use_rag and retrieval_status == "EVIDENCE_FOUND" and _is_marker_only_no_evidence_answer(
            response_payload.get("answer"),
        ):
            retrieval_status = NO_EVIDENCE_MARKER
            context["retrieval_status"] = retrieval_status
            warnings = [_no_evidence_warning_for_context(context)]
            context["warnings"] = warnings
            fallback_started_at = time.perf_counter()
            internal_result = ask_chat(
                message=_build_model_internal_prompt(request.message),
                provider=provider,
                model=model,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                use_rag=True,
            )
            internal_result["latency_ms"] = int((time.perf_counter() - fallback_started_at) * 1000)
            internal_result["warnings"] = warnings
            internal_response = _build_model_internal_chat_response(
                result=internal_result,
                context=context,
                provider=provider,
                model=model,
                temperature=temperature,
                temperature_ignored=temperature_ignored,
                use_rag=True,
                retrieval_status=retrieval_status,
            )
            final_answer = internal_response.answer
            answer_mode = internal_response.answer_mode or ANSWER_MODE_MODEL_INTERNAL
            return internal_response

        final_answer, answer_mode = _finalize_rag_answer(
            retrieval_status=retrieval_status,
            raw_answer=response_payload.get("answer"),
        )
        response_payload["answer"] = final_answer
        evidence_used = _evidence_used_from_payload(
            chunk_ids=chunk_ids,
            document_ids=document_ids,
            source_filenames=source_filenames,
        )
        fallback_used = _fallback_used_from_state(
            retrieval_status=retrieval_status,
            answer_mode=answer_mode,
            evidence_used=evidence_used,
        )

        return ChatResponse(
            **response_payload,
            retrieval_status=retrieval_status,
            answer_mode=answer_mode,
            query_original=context.get("query_original"),
            query_normalized=context.get("query_normalized"),
            query_terms=context.get("query_terms", []),
            quoted_terms=context.get("quoted_terms", []),
            source_intent=context.get("source_intent"),
            selected_corpus=context.get("selected_corpus"),
            active_document_id=context.get("active_document_id"),
            active_document_title=context.get("active_document_title"),
            active_context_used=bool(context.get("active_context_used")),
            active_context_reason=context.get("active_context_reason"),
            evidence_used=evidence_used,
            fallback_used=fallback_used,
            query_expansion_used=bool(context.get("query_expansion_used")),
            query_expansion_reason=context.get("query_expansion_reason"),
            expanded_query_terms=context.get("expanded_query_terms", []),
            candidate_filenames=context.get("candidate_filenames", []),
            selected_filenames=context.get("selected_filenames", []),
            chunks=chunk_texts,
            chunk_ids=chunk_ids,
            document_ids=document_ids,
            source_filenames=source_filenames,
            scores=context.get("scores", []),
            warnings=context.get("warnings", []),
        )

    except LLMClientError as exc:
        error_code = exc.code
        http_status = 502
        if exc.code == "invalid_provider_model_pair":
            http_status = 400
        elif exc.code in {"llm_unavailable", "llm_network_error"}:
            http_status = 503
        elif exc.code in {"llm_timeout"}:
            http_status = 504
        elif exc.code == "llm_model_not_available":
            http_status = 404
        elif exc.code == "llm_auth_error":
            http_status = 401
        elif exc.code == "llm_rate_limited":
            http_status = 429
        raise HTTPException(
            status_code=http_status,
            detail={
                "trace_id": trace_id,
                "status": "error",
                "code": exc.code,
                "message": "No se pudo generar respuesta del modelo.",
                "retrieval_status": retrieval_status,
                "chunk_ids": context.get("chunk_ids", []),
                "document_ids": context.get("document_ids", []),
                "source_filenames": context.get("source_filenames", []),
                "query_original": context.get("query_original"),
                "use_rag": use_rag,
                "warnings": context.get("warnings", []),
            },
        )
    finally:
        log_event(
            component="fastapi.chat",
            event="fastapi.chat.completed" if status == "ok" else "fastapi.chat.failed",
            trace_id=trace_id,
            endpoint="/chat",
            chat_id=request.chat_id,
            user_id=request.user_id,
            provider=provider,
            model=model,
            temperature=temperature,
            temperature_ignored=temperature_ignored,
            use_rag=use_rag,
            status=status,
            latency_ms=int((time.perf_counter() - started_at) * 1000),
            error_code=error_code,
            error_type=error_code,
            retrieval_status=retrieval_status,
            rag_enabled=use_rag,
            message_length=len(request.message),
            chunks_found=len(context.get("chunks", [])),
            query_original=context.get("query_original"),
            query_normalized=context.get("query_normalized"),
            query_terms=context.get("query_terms", []),
            quoted_terms=context.get("quoted_terms", []),
            source_intent=context.get("source_intent"),
            selected_corpus=context.get("selected_corpus"),
            active_document_id=context.get("active_document_id"),
            active_document_title=context.get("active_document_title"),
            active_context_used=bool(context.get("active_context_used")),
            active_context_reason=context.get("active_context_reason"),
            evidence_used=_evidence_used_from_payload(
                chunk_ids=context.get("chunk_ids", []),
                document_ids=context.get("document_ids", []),
                source_filenames=context.get("source_filenames", []),
            ),
            fallback_used=_fallback_used_from_state(
                retrieval_status=retrieval_status,
                answer_mode=answer_mode,
                evidence_used=_evidence_used_from_payload(
                    chunk_ids=context.get("chunk_ids", []),
                    document_ids=context.get("document_ids", []),
                    source_filenames=context.get("source_filenames", []),
                ),
            ),
            query_expansion_used=bool(context.get("query_expansion_used")),
            query_expansion_reason=context.get("query_expansion_reason"),
            expanded_query_terms=context.get("expanded_query_terms", []),
            candidate_filenames=context.get("candidate_filenames", []),
            selected_filenames=context.get("selected_filenames", []),
            chunk_ids=context.get("chunk_ids", []),
            document_ids=context.get("document_ids", []),
            source_filenames=context.get("source_filenames", []),
            scores=context.get("scores", []),
            answer_mode=answer_mode,
            warnings=context.get("warnings", []),
            final_message_preview=_message_preview(final_answer) if final_answer else "",
        )
