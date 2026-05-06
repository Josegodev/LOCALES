import json
import time

from fastapi import FastAPI, HTTPException
from DB.chunks.document_context import build_document_prompt
from app.config import settings
from app.schemas import ChatRequest, ChatResponse
from app.lmstudio_client import ask_lmstudio, LLMError
from app.schemas import CreateDocumentRequest, DocumentCreateResponse
from app.document_writer import create_document, DocumentWriteError
from app.telegram_permissions import TelegramPermissionConfigError, is_telegram_user_allowed


app = FastAPI(title="Local LLM Gateway")


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
        print(
            json.dumps(
                {
                    "component": "fastapi.documents",
                    "request_id": request.request_id,
                    "command": "doc.create",
                    "user_id": request.user_id,
                    "chat_id": request.chat_id,
                    "filename": request.filename,
                    "status": status,
                    "reason": reason,
                    "duration_ms": int((time.perf_counter() - started_at) * 1000),
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
            flush=True,
        )

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    try:
        context = build_document_prompt(request.message, limit=request.top_k or 3)

        print("RAG status:", context["status"], flush=True)
        print("Chunks:", [c["id"] for c in context["chunks"]], flush=True)

        if context["status"] != "EVIDENCE_FOUND":
            return ChatResponse(
                status="ok",
                model=request.model or settings.default_model,
                answer="NO_EVIDENCE_FOR_ANSWER",
                latency_ms=0,
                retrieval_status=context["status"],
                chunks=[],
            )

        result = ask_lmstudio(
            message=context["prompt"],
            model=request.model,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
        )

        return ChatResponse(
            **result,
            retrieval_status=context["status"],
            chunks=[c["id"] for c in context["chunks"]],
        )

    except LLMError as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "status": "error",
                "code": exc.code,
                "message": exc.message,
            },
        )
