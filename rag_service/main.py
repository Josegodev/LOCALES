from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel, Field

from DB.chunks import document_context
from DB.chunks.document_context import normalize_query, normalize_terms
from app.config import settings
from scripts.audit_documents_db import audit_documents_db

NO_EVIDENCE_MARKER = "NO_EVIDENCE_FOR_ANSWER"
MARKER_ONLY_RETRIEVAL_STATUSES = {"NO_EVIDENCE", NO_EVIDENCE_MARKER}

app = FastAPI(title="LOCALES Remote RAG Service")


class RagQueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000)
    top_k: int = Field(default=settings.rag_top_k, ge=1, le=10)
    trace_id: str | None = None
    allowed_source_filenames: list[str] | None = None


def _sanitize_chunk(chunk: dict) -> dict:
    allowed_keys = {
        "id",
        "document_id",
        "filename",
        "corpus",
        "source_type",
        "priority",
        "chunk_index",
        "char_count",
        "text",
        "score",
        "quoted_matches",
        "matched_terms",
        "expanded_matches",
    }
    return {
        key: value
        for key, value in chunk.items()
        if key in allowed_keys
    }


def _no_evidence_response(
    *,
    query: str,
    top_k: int,
    trace_id: str | None,
    code: str,
    message: str,
) -> dict:
    return {
        "status": NO_EVIDENCE_MARKER,
        "retrieval_status": NO_EVIDENCE_MARKER,
        "evidence_used": False,
        "fallback_used": True,
        "prompt": (
            "No hay evidencia documental suficiente para responder.\n\n"
            f"PREGUNTA:\n{query}\n\n"
            "Responde exactamente: NO_EVIDENCE_FOR_ANSWER"
        ),
        "chunks_found": 0,
        "chunks": [],
        "chunk_ids": [],
        "document_ids": [],
        "source_filenames": [],
        "scores": [],
        "warnings": [
            {
                "code": code,
                "message": message,
            }
        ],
        "trace_id": trace_id,
        "top_k": top_k,
        "query_original": query,
        "query_normalized": normalize_query(query),
        "query_terms": normalize_terms(query),
        "quoted_terms": [],
        "candidate_filenames": [],
        "selected_filenames": [],
    }


def _configure_documents_db_path() -> None:
    document_context.DB_PATH = Path(settings.documents_db_path)


def _normalize_retrieval_status(value: str) -> str:
    if value in MARKER_ONLY_RETRIEVAL_STATUSES:
        return NO_EVIDENCE_MARKER
    return value


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/rag/health")
def rag_health() -> dict:
    return audit_documents_db(settings.documents_db_path)


@app.post("/rag/query")
def rag_query(request: RagQueryRequest) -> dict:
    _configure_documents_db_path()
    try:
        context = document_context.build_document_prompt(
            request.query,
            limit=request.top_k,
            allowed_source_filenames=request.allowed_source_filenames,
        )
    except Exception as exc:
        return _no_evidence_response(
            query=request.query,
            top_k=request.top_k,
            trace_id=request.trace_id,
            code="RAG_DB_INVALID",
            message=str(exc),
        )

    chunks = [
        _sanitize_chunk(chunk)
        for chunk in context.get("chunks", [])
        if isinstance(chunk, dict)
    ]
    retrieval_status = _normalize_retrieval_status(
        str(context.get("retrieval_status") or context.get("status") or NO_EVIDENCE_MARKER)
    )

    return {
        **context,
        "status": retrieval_status,
        "retrieval_status": retrieval_status,
        "evidence_used": retrieval_status == "EVIDENCE_FOUND" and bool(chunks),
        "fallback_used": retrieval_status != "EVIDENCE_FOUND",
        "chunks_found": len(chunks),
        "chunks": chunks,
        "warnings": context.get("warnings", []),
        "trace_id": request.trace_id,
        "top_k": request.top_k,
    }
