import re
import time

from fastapi import FastAPI, HTTPException
from DB.chunks.document_context import build_document_prompt
from app.observability import new_trace_id
from app.observability import log_event
from app.llm_client import LLMClientError, ask_chat, resolve_provider_model
from app.schemas import ChatRequest, ChatResponse
from app.schemas import CreateDocumentRequest, DocumentCreateResponse
from app.document_writer import create_document, DocumentWriteError
from app.telegram_permissions import TelegramPermissionConfigError, is_telegram_user_allowed

NO_EVIDENCE_MARKER = "NO_EVIDENCE_FOR_ANSWER"
NO_EVIDENCE_EXPLANATION = "No hay evidencia documental suficiente para responder."


app = FastAPI(title="Local LLM Gateway")


def _no_evidence_answer() -> str:
    return f"{NO_EVIDENCE_MARKER}\n{NO_EVIDENCE_EXPLANATION}"


def _extract_anchor_terms(query: str) -> list[str]:
    terms = re.findall(r"[\w:-]+", query.lower())
    return [
        term
        for term in terms
        if len(term) >= 8 and (any(character.isdigit() for character in term) or "_" in term or "-" in term)
    ]


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


def _extract_chunk_response_data(chunks: list[dict]) -> tuple[list[str], list[int]]:
    chunk_texts: list[str] = []
    chunk_ids: list[int] = []

    for chunk in chunks:
        if not isinstance(chunk, dict):
            continue

        chunk_text = chunk.get("text")
        if isinstance(chunk_text, str) and chunk_text.strip():
            chunk_texts.append(chunk_text)

        chunk_id = chunk.get("id")
        if isinstance(chunk_id, int):
            chunk_ids.append(chunk_id)
            continue

        if isinstance(chunk_id, str) and chunk_id.isdigit():
            chunk_ids.append(int(chunk_id))

    return chunk_texts, chunk_ids


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


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

    try:
        provider, model = resolve_provider_model(provider, request.model)
        context = build_document_prompt(request.message, limit=request.top_k or 3)
        retrieval_status = str(context["status"])
        if context["status"] == "EVIDENCE_FOUND" and _should_force_no_evidence(
            request.message,
            context.get("chunks", []),
        ):
            retrieval_status = "NO_EVIDENCE"

        if retrieval_status != "EVIDENCE_FOUND":
            status = "ok"
            return ChatResponse(
                status="ok",
                provider=provider,
                model=model,
                temperature=temperature,
                temperature_ignored=False,
                answer=_no_evidence_answer(),
                latency_ms=0,
                retrieval_status=retrieval_status,
                chunks=[],
                chunk_ids=[],
            )

        llm_started_at = time.perf_counter()
        result = ask_chat(
            message=context["prompt"],
            provider=provider,
            model=model,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
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
        status = "ok"
        chunk_texts, chunk_ids = _extract_chunk_response_data(context.get("chunks", []))
        response_payload = dict(result)
        if not isinstance(response_payload.get("provider"), str) or not response_payload["provider"].strip():
            response_payload["provider"] = provider
        if not isinstance(response_payload.get("temperature"), (int, float)):
            response_payload["temperature"] = temperature
        if not isinstance(response_payload.get("temperature_ignored"), bool):
            response_payload["temperature_ignored"] = temperature_ignored

        return ChatResponse(
            **response_payload,
            retrieval_status=retrieval_status,
            chunks=chunk_texts,
            chunk_ids=chunk_ids,
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
            },
        )
    except Exception as exc:
        error_code = exc.__class__.__name__
        raise HTTPException(
            status_code=500,
            detail={
                "trace_id": trace_id,
                "status": "error",
                "code": "chat_internal_error",
                "message": str(exc)[:500],
            },
        )
    finally:
        log_event(
            component="fastapi.chat",
            event="fastapi.chat.completed" if status == "ok" else "fastapi.chat.failed",
            trace_id=trace_id,
            chat_id=request.chat_id,
            user_id=request.user_id,
            provider=provider,
            model=model,
            temperature=temperature,
            temperature_ignored=temperature_ignored,
            status=status,
            latency_ms=int((time.perf_counter() - started_at) * 1000),
            error_code=error_code,
            retrieval_status=retrieval_status,
        )
