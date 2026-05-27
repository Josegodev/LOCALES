from __future__ import annotations

import requests

from app.config import settings
from DB.chunks.document_context import normalize_query, normalize_terms

NO_EVIDENCE_MARKER = "NO_EVIDENCE_FOR_ANSWER"


def _controlled_no_evidence(
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
        "chunks": [],
        "chunks_found": 0,
        "chunk_ids": [],
        "document_ids": [],
        "source_filenames": [],
        "scores": [],
        "ranking_scores": [],
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


def query_remote_rag(
    query: str,
    top_k: int,
    trace_id: str | None = None,
    allowed_source_filenames: list[str] | None = None,
    active_document_id: int | None = None,
    active_document_title: str | None = None,
    active_corpus: str | None = None,
    last_source_intent: str | None = None,
) -> dict:
    payload = {
        "query": query,
        "top_k": top_k,
        "trace_id": trace_id,
    }
    if allowed_source_filenames:
        payload["allowed_source_filenames"] = allowed_source_filenames
    if active_document_id is not None:
        payload["active_document_id"] = active_document_id
    if active_document_title:
        payload["active_document_title"] = active_document_title
    if active_corpus:
        payload["active_corpus"] = active_corpus
    if last_source_intent:
        payload["last_source_intent"] = last_source_intent

    try:
        response = requests.post(
            f"{settings.rag_service_base_url()}/rag/query",
            json=payload,
            timeout=settings.rag_timeout_seconds,
        )
    except (requests.Timeout, requests.ConnectionError):
        return _controlled_no_evidence(
            query=query,
            top_k=top_k,
            trace_id=trace_id,
            code="RAG_SERVICE_UNAVAILABLE",
            message="Remote RAG service is unavailable.",
        )

    if response.status_code >= 500:
        return _controlled_no_evidence(
            query=query,
            top_k=top_k,
            trace_id=trace_id,
            code="RAG_SERVICE_ERROR",
            message="Remote RAG service returned an internal error.",
        )

    response.raise_for_status()
    payload = response.json()
    if isinstance(payload, dict):
        payload.setdefault("status", payload.get("retrieval_status", NO_EVIDENCE_MARKER))
        payload.setdefault("trace_id", trace_id)
        return payload

    return _controlled_no_evidence(
        query=query,
        top_k=top_k,
        trace_id=trace_id,
        code="RAG_SERVICE_INVALID_RESPONSE",
        message="Remote RAG service returned a non-object JSON response.",
    )
