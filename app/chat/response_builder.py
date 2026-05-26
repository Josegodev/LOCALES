from __future__ import annotations

from typing import Any

from app.schemas import ChatResponse


def normalize_public_warnings(value: Any) -> list[str | dict]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, (str, dict))]


def build_chat_response(
    *,
    trace_id: str,
    response_payload: dict[str, Any],
    context: dict[str, Any],
    retrieval_status: str,
    answer_mode: str,
    evidence_used: bool,
    fallback_used: bool,
    chunk_texts: list[str],
    chunk_ids: list[int],
    document_ids: list[int],
    source_filenames: list[str],
) -> ChatResponse:
    normalized_payload = dict(response_payload)
    normalized_warnings = normalize_public_warnings(context.get("warnings", []))

    return ChatResponse(
        trace_id=trace_id,
        **normalized_payload,
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
        warnings=normalized_warnings,
    )
