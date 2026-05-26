from __future__ import annotations

import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from DB.chunks.document_context import detect_source_intent, normalize_terms
from app.schemas import ChatRequest

NO_EVIDENCE_MARKER = "NO_EVIDENCE_FOR_ANSWER"
MARKER_ONLY_RETRIEVAL_STATUSES = {"NO_EVIDENCE", "NO_EVIDENCE_FOR_ANSWER"}
COMMON_QUERY_TERMS = {
    "about",
    "busca",
    "cosa",
    "dice",
    "does",
    "donde",
    "dónde",
    "evidencia",
    "existe",
    "mean",
    "meaning",
    "paper",
    "que",
    "qué",
    "say",
    "significa",
    "sobre",
    "thing",
    "what",
}


@dataclass(slots=True)
class RetrievalResult:
    retrieval_status: str
    evidence_used: bool
    context_text: str
    chunk_texts: list[str]
    chunk_ids: list[int]
    document_ids: list[int]
    source_filenames: list[str]
    candidate_filenames: list[str]
    retrieval_latency_ms: int | None
    warnings: list[str | dict]
    fallback_used: bool
    fallback_reason: str | None
    context: dict[str, Any]


def _build_default_context(message: str, *, use_rag: bool) -> dict[str, Any]:
    return {
        "status": "DISABLED" if not use_rag else "unknown",
        "retrieval_status": "DISABLED" if not use_rag else "unknown",
        "prompt": message,
        "query_original": message,
        "query_normalized": message.strip().casefold(),
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


def _normalize_no_evidence_retrieval_status(value: str) -> str:
    if value in MARKER_ONLY_RETRIEVAL_STATUSES:
        return NO_EVIDENCE_MARKER
    return value


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


def retrieve_chat_context(
    *,
    request: ChatRequest,
    trace_id: str,
    use_rag: bool,
    settings_obj,
    build_document_prompt_fn,
    query_remote_rag_fn,
) -> RetrievalResult:
    context = _build_default_context(request.message, use_rag=use_rag)
    retrieval_latency_ms: int | None = None

    active_document_title = _normalize_active_document_title(request.active_document_title)
    use_active_context, active_context_reason = _should_use_active_context(
        query=request.message,
        active_document_id=request.active_document_id,
        active_document_title=active_document_title,
    )

    if use_rag:
        retrieval_started_at = time.perf_counter()
        top_k = request.top_k or 3
        if settings_obj.use_remote_rag:
            context = query_remote_rag_fn(
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
            context = build_document_prompt_fn(
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

        retrieval_latency_ms = int((time.perf_counter() - retrieval_started_at) * 1000)
    else:
        retrieval_status = "DISABLED"
        context["retrieval_status"] = retrieval_status

    chunk_texts, chunk_ids, document_ids, source_filenames = (
        _extract_chunk_response_data(context.get("chunks", [])) if use_rag else ([], [], [], [])
    )
    context["chunk_ids"] = list(chunk_ids)
    context["document_ids"] = list(document_ids)
    context["source_filenames"] = list(source_filenames)

    evidence_used = (
        bool(chunk_ids or document_ids or source_filenames)
        and retrieval_status not in MARKER_ONLY_RETRIEVAL_STATUSES
        and retrieval_status != "DISABLED"
    )
    fallback_used = retrieval_status in MARKER_ONLY_RETRIEVAL_STATUSES
    fallback_reason = "no_evidence" if fallback_used else None

    return RetrievalResult(
        retrieval_status=retrieval_status,
        evidence_used=evidence_used,
        context_text=context.get("prompt") if isinstance(context.get("prompt"), str) else request.message,
        chunk_texts=chunk_texts,
        chunk_ids=chunk_ids,
        document_ids=document_ids,
        source_filenames=source_filenames,
        candidate_filenames=list(context.get("candidate_filenames", [])),
        retrieval_latency_ms=retrieval_latency_ms,
        warnings=list(context.get("warnings", [])),
        fallback_used=fallback_used,
        fallback_reason=fallback_reason,
        context=context,
    )
