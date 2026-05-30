from __future__ import annotations

from app.chat.response_builder import build_chat_response
from app.llm_errors import LLMClientError
from app.chat.retrieval import MARKER_ONLY_RETRIEVAL_STATUSES, NO_EVIDENCE_MARKER

NO_EVIDENCE_EXPLANATION = "No hay evidencia documental suficiente para responder."
ANSWER_MODE_DOCUMENTARY = "documentary_answer"
ANSWER_MODE_SAFE_REFUSAL = "safe_refusal"
ANSWER_MODE_STANDARD = "standard_answer"
ACTIVE_CONTEXT_NO_EVIDENCE_WARNING = (
    "Contexto activo detectado, pero sin chunks documentales suficientes para responder."
)
NO_EVIDENCE_WARNING = "No hay evidencia documental local suficiente para responder."


def no_evidence_answer() -> str:
    return f"{NO_EVIDENCE_MARKER}\n{NO_EVIDENCE_EXPLANATION}"


def normalize_no_evidence_retrieval_status(value: str) -> str:
    if value in MARKER_ONLY_RETRIEVAL_STATUSES:
        return NO_EVIDENCE_MARKER
    return value


def strip_no_evidence_markers(answer: str) -> str:
    normalized = answer.replace("\r\n", "\n").replace("\r", "\n")
    for token in (NO_EVIDENCE_MARKER, NO_EVIDENCE_EXPLANATION):
        normalized = normalized.replace(token, "")
    lines = [line.strip() for line in normalized.split("\n") if line.strip()]
    return "\n".join(lines).strip()


def is_marker_only_no_evidence_answer(answer: str | None) -> bool:
    if not isinstance(answer, str):
        return False

    normalized = answer.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        return False

    if NO_EVIDENCE_MARKER not in normalized and NO_EVIDENCE_EXPLANATION not in normalized:
        return False

    return not strip_no_evidence_markers(normalized)


def finalize_rag_answer(
    *,
    retrieval_status: str,
    raw_answer: str | None,
) -> tuple[str, str]:
    if retrieval_status in MARKER_ONLY_RETRIEVAL_STATUSES:
        return no_evidence_answer(), ANSWER_MODE_SAFE_REFUSAL

    candidate = raw_answer if isinstance(raw_answer, str) else ""

    if retrieval_status != "EVIDENCE_FOUND":
        cleaned = candidate.strip()
        if not cleaned:
            raise LLMClientError(
                "rag_answer_contract_invalid",
                "standard_answer_empty",
            )
        return cleaned, ANSWER_MODE_STANDARD

    cleaned = strip_no_evidence_markers(candidate)

    if not cleaned:
        raise LLMClientError(
            "rag_answer_contract_invalid",
            "documentary_answer_empty_after_sanitization",
        )

    return cleaned, ANSWER_MODE_DOCUMENTARY


def fallback_used_from_state(
    *,
    retrieval_status: str | None,
    answer_mode: str | None,
    evidence_used: bool,
) -> bool:
    if retrieval_status in MARKER_ONLY_RETRIEVAL_STATUSES:
        return True
    return not evidence_used and answer_mode == ANSWER_MODE_SAFE_REFUSAL


def fallback_reason_from_state(
    *,
    retrieval_status: str | None,
    answer_mode: str | None,
    evidence_used: bool,
) -> str | None:
    if not fallback_used_from_state(
        retrieval_status=retrieval_status,
        answer_mode=answer_mode,
        evidence_used=evidence_used,
    ):
        return None
    if answer_mode == ANSWER_MODE_SAFE_REFUSAL:
        return "safe_refusal_no_evidence"
    if retrieval_status in MARKER_ONLY_RETRIEVAL_STATUSES:
        return "no_evidence"
    return "fallback_used"


def no_evidence_warning_for_context(context: dict) -> str:
    if bool(context.get("active_context_used")):
        return ACTIVE_CONTEXT_NO_EVIDENCE_WARNING
    return NO_EVIDENCE_WARNING


def _clear_evidence_trace(context: dict) -> None:
    for key in (
        "chunks",
        "chunk_ids",
        "document_ids",
        "source_filenames",
        "selected_filenames",
        "scores",
    ):
        context[key] = []


def clear_evidence_trace(context: dict) -> None:
    _clear_evidence_trace(context)


def build_safe_refusal_chat_response(
    *,
    trace_id: str,
    context: dict,
    provider: str,
    model: str,
    temperature: float,
    temperature_ignored: bool,
    use_rag: bool,
    latency_ms: int,
):
    response_warnings = list(context.get("warnings", []))
    no_evidence_warning = no_evidence_warning_for_context(context)
    if no_evidence_warning not in response_warnings:
        response_warnings.append(no_evidence_warning)
    context["warnings"] = response_warnings
    _clear_evidence_trace(context)

    return build_chat_response(
        trace_id=trace_id,
        response_payload={
            "status": "ok",
            "provider": provider,
            "model": model,
            "temperature": temperature,
            "temperature_ignored": temperature_ignored,
            "use_rag": use_rag,
            "answer": no_evidence_answer(),
            "latency_ms": latency_ms,
        },
        context=context,
        retrieval_status=NO_EVIDENCE_MARKER,
        answer_mode=ANSWER_MODE_SAFE_REFUSAL,
        evidence_used=False,
        fallback_used=True,
        chunk_texts=[],
        chunk_ids=[],
        document_ids=[],
        source_filenames=[],
    )
