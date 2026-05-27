# Transitional compatibility path.
# New code should pass dependencies explicitly.
# Fallback imports must be removed once ChatService owns retrieval/generation/persistence.

import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

from fastapi import HTTPException

from DB.chunks.document_context import (
    build_document_prompt,
    detect_source_intent,
    is_referential_query,
    normalize_terms,
    source_intent_from_corpus_hint,
)
from app.config import settings
from app.llm_client import LLMClientError, ask_chat, resolve_provider_model
from app.observability.chat_runs import save_chat_run
from app.observability.logging import log_event
from app.observability.trace import new_trace_id
from app.rag_client import query_remote_rag
from app.schemas import ChatRequest, ChatResponse, TEMPERATURE_DEFAULT
from app.tools.create_document import (
    CREATE_DOCUMENT_SYSTEM_PROMPT,
    build_create_document_request,
    create_document_tool,
)

if TYPE_CHECKING:
    from app.chat.dependencies import ChatDependencies

NO_EVIDENCE_MARKER = "NO_EVIDENCE_FOR_ANSWER"
NO_EVIDENCE_EXPLANATION = "No hay evidencia documental suficiente para responder."
ANSWER_MODE_DOCUMENTARY = "documentary_answer"
ANSWER_MODE_SAFE_REFUSAL = "safe_refusal"
ANSWER_MODE_STANDARD = "standard_answer"
MARKER_ONLY_RETRIEVAL_STATUSES = {"NO_EVIDENCE", "NO_EVIDENCE_FOR_ANSWER"}
ACTIVE_CONTEXT_NO_EVIDENCE_WARNING = (
    "Contexto activo detectado, pero sin chunks documentales suficientes para responder."
)
NO_EVIDENCE_WARNING = "No hay evidencia documental local suficiente para responder."
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
CREATE_DOCUMENT_COMMAND = "creardoc"
CREATE_DOCUMENT_PREFIX = "/creardoc"


def _no_evidence_answer() -> str:
    return f"{NO_EVIDENCE_MARKER}\n{NO_EVIDENCE_EXPLANATION}"


def _message_preview(text: str, limit: int = 200) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[:limit].rstrip() + "..."


def parse_chat_command(message: str) -> dict | None:
    if not isinstance(message, str):
        return None
    stripped_message = message.strip()
    if not stripped_message:
        return None
    if not stripped_message.casefold().startswith(CREATE_DOCUMENT_PREFIX):
        return None

    instruction = stripped_message[len(CREATE_DOCUMENT_PREFIX):].strip()
    return {
        "command": CREATE_DOCUMENT_COMMAND,
        "instruction": instruction,
    }


def _chat_trace_source(user_id: int | None, chat_id: int | None) -> str:
    return "chat"


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
        "scores",
        "ranking_scores",
    ):
        context[key] = []


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
    if retrieval_status in MARKER_ONLY_RETRIEVAL_STATUSES:
        return True
    return not evidence_used and answer_mode == ANSWER_MODE_SAFE_REFUSAL


def _fallback_reason_from_state(
    *,
    retrieval_status: str | None,
    answer_mode: str | None,
    evidence_used: bool,
) -> str | None:
    if not _fallback_used_from_state(
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


def _no_evidence_warning_for_context(context: dict) -> str:
    if bool(context.get("active_context_used")):
        return ACTIVE_CONTEXT_NO_EVIDENCE_WARNING
    return NO_EVIDENCE_WARNING


def _build_safe_refusal_chat_response(
    *,
    trace_id: str,
    context: dict,
    provider: str,
    model: str,
    temperature: float,
    temperature_ignored: bool,
    use_rag: bool,
    latency_ms: int,
) -> ChatResponse:
    response_warnings = list(context.get("warnings", []))
    no_evidence_warning = _no_evidence_warning_for_context(context)
    if no_evidence_warning not in response_warnings:
        response_warnings.append(no_evidence_warning)
    context["warnings"] = response_warnings
    _clear_evidence_trace(context)

    return ChatResponse(
        trace_id=trace_id,
        status="ok",
        provider=provider,
        model=model,
        temperature=temperature,
        temperature_ignored=temperature_ignored,
        use_rag=use_rag,
        answer=_no_evidence_answer(),
        latency_ms=latency_ms,
        retrieval_status=NO_EVIDENCE_MARKER,
        answer_mode=ANSWER_MODE_SAFE_REFUSAL,
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
        candidate_filenames=context.get("candidate_filenames", []),
        selected_filenames=[],
        chunks=[],
        chunk_ids=[],
        document_ids=[],
        source_filenames=[],
        scores=[],
        ranking_scores=[],
        warnings=response_warnings,
    )


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
    active_corpus: str | None = None,
    last_source_intent: str | None = None,
) -> tuple[bool, str | None]:
    if active_document_id is None and not active_document_title:
        return False, None

    source_intent = detect_source_intent(
        query,
        active_corpus=active_corpus,
        last_source_intent=last_source_intent,
    )
    query_terms = normalize_terms(query)
    query_word_count = len(query.strip().split())
    referential_query = is_referential_query(query)
    is_short_or_ambiguous = referential_query or len(query_terms) <= 2 or query_word_count <= 4
    if not is_short_or_ambiguous:
        return False, "query_specific_enough"

    active_document_intent = source_intent_from_corpus_hint(active_corpus)
    if active_document_intent is None and isinstance(active_document_title, str):
        normalized_title = active_document_title.strip().casefold()
        if normalized_title.endswith(".pdf"):
            active_document_intent = "official_docs"
        elif normalized_title.endswith(".md"):
            active_document_intent = "nucleo"

    if source_intent != "mixed" and active_document_intent and source_intent != active_document_intent:
        return False, "overridden_by_explicit_intent"

    if referential_query:
        return True, "referential_query"

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


def _dependency_or_default(
    dependencies: "ChatDependencies | None",
    attribute: str,
    default: Any,
) -> Any:
    if dependencies is None:
        return default
    value = getattr(dependencies, attribute, None)
    if value is None:
        return default
    return value


def _persist_chat_run(
    *,
    save_chat_run_fn,
    trace_id: str,
    request: ChatRequest,
    final_answer: str,
    provider: str,
    requested_model: str | None,
    model: str | None,
    temperature: float,
    max_tokens: int | None,
    top_p: float | None,
    status: str,
    retrieval_status: str,
    chunk_ids: list[int],
    document_ids: list[int],
    source_filenames: list[str],
    latency_ms: int,
    generation_latency_ms: int | None,
    retrieval_latency_ms: int | None,
    tool_latency_ms: int | None,
    error_code: str | None,
    error_message: str | None,
    warnings: list[str],
    use_rag: bool,
    evidence_used: bool,
    fallback_used: bool,
    fallback_reason: str | None,
    answer_mode: str | None,
    tokens_input: int | float | None,
    tokens_output: int | float | None,
    tokens_total: int | float | None,
    prompt_eval_count: int | float | None,
    eval_count: int | float | None,
    prompt_eval_duration: int | float | None,
    eval_duration: int | float | None,
    total_duration: int | float | None,
    load_duration: int | float | None,
    trace_source: str,
    command: str | None,
    tool_called: str | None,
    tool_result_status: str | None,
    document_path: str | None,
    document_filename: str | None,
    chars_written: int | None,
    overwrite_requested: bool | None,
    overwrite_applied: bool | None,
    overwrite_reason: str | None,
    source_intent: str | None,
    selected_corpus: str | None,
    active_document_id: int | None,
    active_document_title: str | None,
    active_context_used: bool,
    ranking_scores: list[int],
) -> None:
    created_at = datetime.now(timezone.utc).isoformat()
    save_chat_run_fn(
        {
            "trace_id": trace_id,
            "created_at": created_at,
            "timestamp": created_at,
            "source": trace_source,
            "endpoint": "/chat",
            "input": request.message,
            "response": final_answer or None,
            "provider": provider,
            "requested_model": requested_model,
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
            "generation_config": {
                key: value
                for key, value in {
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "top_p": top_p,
                }.items()
                if value is not None
            } or None,
            "status": status,
            "retrieval_status": retrieval_status,
            "chunk_ids": chunk_ids,
            "document_ids": document_ids,
            "source_filenames": source_filenames,
            "source_intent": source_intent,
            "selected_corpus": selected_corpus,
            "active_document_id": active_document_id,
            "active_document_title": active_document_title,
            "active_context_used": active_context_used,
            "ranking_scores": ranking_scores,
            "latency_ms": latency_ms,
            "generation_latency_ms": generation_latency_ms,
            "retrieval_latency_ms": retrieval_latency_ms,
            "tool_latency_ms": tool_latency_ms,
            "error_code": error_code,
            "error_message": error_message,
            "warnings": warnings,
            "tokens_input": tokens_input,
            "tokens_output": tokens_output,
            "tokens_total": tokens_total,
            "prompt_eval_count": prompt_eval_count,
            "eval_count": eval_count,
            "prompt_eval_duration": prompt_eval_duration,
            "eval_duration": eval_duration,
            "total_duration": total_duration,
            "load_duration": load_duration,
            "use_rag": use_rag,
            "evidence_used": evidence_used,
            "fallback_used": fallback_used,
            "fallback_reason": fallback_reason,
            "answer_mode": answer_mode,
            "command": command,
            "tool_called": tool_called,
            "tool_result_status": tool_result_status,
            "document_path": document_path,
            "document_filename": document_filename,
            "chars_written": chars_written,
            "overwrite_requested": overwrite_requested,
            "overwrite_applied": overwrite_applied,
            "overwrite_reason": overwrite_reason,
            "error_type": error_code,
        }
    )


def _run_create_document_command(
    *,
    ask_chat_fn,
    create_document_tool_fn,
    request: ChatRequest,
    trace_id: str,
    provider: str,
    model: str,
    temperature: float,
    top_p: float | None,
    effective_max_tokens: int | None,
) -> tuple[ChatResponse, dict]:
    parsed_command = parse_chat_command(request.message)
    instruction = parsed_command.get("instruction", "") if isinstance(parsed_command, dict) else ""
    if not instruction:
        raise HTTPException(
            status_code=400,
            detail={
                "trace_id": trace_id,
                "status": "error",
                "code": "missing_instruction",
                "message": "El comando /creardoc requiere una instruccion despues del prefijo.",
                "retrieval_status": "DISABLED",
                "chunk_ids": [],
                "document_ids": [],
                "source_filenames": [],
                "query_original": request.message,
                "use_rag": False,
                "warnings": [],
                "command": CREATE_DOCUMENT_COMMAND,
                "tool_called": "create_document",
            },
        )

    llm_started_at = time.perf_counter()
    generation_result = ask_chat_fn(
        message=instruction,
        provider=provider,
        model=model,
        max_tokens=request.max_tokens,
        temperature=temperature,
        top_p=top_p,
        use_rag=False,
        system_prompt=CREATE_DOCUMENT_SYSTEM_PROMPT,
    )
    generation_latency_ms = int((time.perf_counter() - llm_started_at) * 1000)
    generation_result["latency_ms"] = generation_latency_ms
    generated_content = generation_result.get("answer")
    if not isinstance(generated_content, str) or not generated_content.strip():
        raise HTTPException(
            status_code=502,
            detail={
                "trace_id": trace_id,
                "status": "error",
                "code": "document_generation_failed",
                "message": "El modelo no devolvio contenido Markdown para /creardoc.",
                "retrieval_status": "DISABLED",
                "chunk_ids": [],
                "document_ids": [],
                "source_filenames": [],
                "query_original": request.message,
                "use_rag": False,
                "warnings": [],
                "command": CREATE_DOCUMENT_COMMAND,
                "tool_called": "create_document",
            },
        )

    document_request = build_create_document_request(
        request_id=trace_id,
        instruction=instruction,
        content=generated_content,
        user_id=request.user_id,
        chat_id=request.chat_id,
        overwrite=False,
    )

    tool_started_at = time.perf_counter()
    tool_result = _run_async_document_tool(
        request=document_request,
        create_document_tool_fn=create_document_tool_fn,
    )
    tool_latency_ms = int((time.perf_counter() - tool_started_at) * 1000)
    if tool_result.get("status") != "ok":
        error_type = tool_result.get("error_type") if isinstance(tool_result.get("error_type"), str) else "document_write_failed"
        raise HTTPException(
            status_code=500,
            detail={
                "trace_id": trace_id,
                "status": "error",
                "code": "document_write_failed",
                "message": tool_result.get("error_message") if isinstance(tool_result.get("error_message"), str) else "No se pudo escribir el documento Markdown.",
                "retrieval_status": "DISABLED",
                "chunk_ids": [],
                "document_ids": [],
                "source_filenames": [],
                "query_original": request.message,
                "use_rag": False,
                "warnings": [],
                "command": CREATE_DOCUMENT_COMMAND,
                "tool_called": "create_document",
                "tool_result_status": tool_result.get("status"),
                "error_type": error_type,
            },
        )

    provider_name = generation_result.get("provider")
    if isinstance(provider_name, str) and provider_name.strip():
        provider = provider_name.strip().lower()
    model_name = generation_result.get("model")
    if isinstance(model_name, str) and model_name.strip():
        model = model_name.strip()
    if isinstance(generation_result.get("temperature"), (int, float)):
        temperature = float(generation_result["temperature"])
    if isinstance(generation_result.get("max_tokens"), int):
        effective_max_tokens = generation_result["max_tokens"]

    response = ChatResponse(
        trace_id=trace_id,
        status="ok",
        provider=provider,
        model=model,
        temperature=temperature,
        temperature_ignored=bool(generation_result.get("temperature_ignored", False)),
        use_rag=False,
        answer=f"Documento creado: {tool_result.get('document_path')}",
        latency_ms=generation_latency_ms + tool_latency_ms,
        retrieval_status="DISABLED",
        answer_mode="tool_result",
        warnings=[],
        tool_latency_ms=tool_latency_ms,
        command=CREATE_DOCUMENT_COMMAND,
        tool_called="create_document",
        tool_result_status=tool_result.get("status") if isinstance(tool_result.get("status"), str) else None,
        document_path=tool_result.get("document_path") if isinstance(tool_result.get("document_path"), str) else None,
        document_filename=tool_result.get("document_filename") if isinstance(tool_result.get("document_filename"), str) else None,
        chars_written=tool_result.get("chars_written") if isinstance(tool_result.get("chars_written"), int) else None,
        overwrite_requested=tool_result.get("overwrite_requested") if isinstance(tool_result.get("overwrite_requested"), bool) else False,
        overwrite_applied=tool_result.get("overwrite_applied") if isinstance(tool_result.get("overwrite_applied"), bool) else False,
        overwrite_reason=tool_result.get("overwrite_reason") if isinstance(tool_result.get("overwrite_reason"), str) else None,
        prompt_eval_count=generation_result.get("prompt_eval_count") if isinstance(generation_result.get("prompt_eval_count"), int) else None,
        eval_count=generation_result.get("eval_count") if isinstance(generation_result.get("eval_count"), int) else None,
        prompt_eval_duration=generation_result.get("prompt_eval_duration") if isinstance(generation_result.get("prompt_eval_duration"), int) else None,
        eval_duration=generation_result.get("eval_duration") if isinstance(generation_result.get("eval_duration"), int) else None,
        total_duration=generation_result.get("total_duration") if isinstance(generation_result.get("total_duration"), int) else None,
        load_duration=generation_result.get("load_duration") if isinstance(generation_result.get("load_duration"), int) else None,
    )
    return response, {
        "generation_latency_ms": generation_latency_ms,
        "tool_latency_ms": tool_latency_ms,
        "provider": provider,
        "model": model,
        "temperature": temperature,
        "effective_max_tokens": effective_max_tokens,
        "tokens_input": generation_result.get("prompt_eval_count"),
        "tokens_output": generation_result.get("eval_count"),
        "tokens_total": generation_result.get("tokens_total"),
        "prompt_eval_count": generation_result.get("prompt_eval_count"),
        "eval_count": generation_result.get("eval_count"),
        "prompt_eval_duration": generation_result.get("prompt_eval_duration"),
        "eval_duration": generation_result.get("eval_duration"),
        "total_duration": generation_result.get("total_duration"),
        "load_duration": generation_result.get("load_duration"),
    }


def _run_async_document_tool(*, request, create_document_tool_fn=None) -> dict:
    import asyncio

    tool_fn = create_document_tool_fn or create_document_tool
    return asyncio.run(tool_fn(request=request))


def run_chat_request(
    request: ChatRequest,
    *,
    persist_trace: bool = True,
    dependencies: "ChatDependencies | None" = None,
) -> ChatResponse:
    ask_chat_fn = _dependency_or_default(dependencies, "ask_chat", ask_chat)
    build_document_prompt_fn = _dependency_or_default(
        dependencies,
        "build_document_prompt",
        build_document_prompt,
    )
    query_remote_rag_fn = _dependency_or_default(dependencies, "query_remote_rag", query_remote_rag)
    resolve_provider_model_fn = _dependency_or_default(
        dependencies,
        "resolve_provider_model",
        resolve_provider_model,
    )
    save_chat_run_fn = _dependency_or_default(dependencies, "save_chat_run", save_chat_run)
    log_event_fn = _dependency_or_default(dependencies, "log_event", log_event)
    new_trace_id_fn = _dependency_or_default(dependencies, "new_trace_id", new_trace_id)
    settings_obj = _dependency_or_default(dependencies, "settings", settings)
    create_document_tool_fn = _dependency_or_default(
        dependencies,
        "create_document_tool",
        create_document_tool,
    )

    trace_id = request.trace_id or new_trace_id_fn()
    requested_model = request.model.strip() if isinstance(request.model, str) and request.model.strip() else None
    started_at = time.perf_counter()
    status = "error"
    error_code: str | None = None
    retrieval_status = "unknown"
    provider = (request.provider or "ollama").strip().lower()
    model = request.model or ""
    temperature = request.temperature if isinstance(request.temperature, (int, float)) else TEMPERATURE_DEFAULT
    top_p = request.top_p if isinstance(request.top_p, (int, float)) else None
    effective_max_tokens = request.max_tokens if isinstance(request.max_tokens, int) else settings_obj.max_tokens
    temperature_ignored = False
    use_rag = True if request.use_rag is None else bool(request.use_rag)
    retrieval_latency_ms: int | None = None
    generation_latency_ms = 0
    answer_mode = "unknown"
    final_answer = ""
    error_message: str | None = None
    trace_source = _chat_trace_source(request.user_id, request.chat_id)
    command: str | None = None
    tool_called: str | None = None
    tool_result_status: str | None = None
    document_path: str | None = None
    document_filename: str | None = None
    chars_written: int | None = None
    overwrite_requested: bool | None = None
    overwrite_applied: bool | None = None
    overwrite_reason: str | None = None
    tool_latency_ms: int | None = None
    response_chunk_ids: list[int] = []
    llm_metrics: dict[str, int | float | None] = {
        "tokens_input": None,
        "tokens_output": None,
        "tokens_total": None,
        "prompt_eval_count": None,
        "eval_count": None,
        "prompt_eval_duration": None,
        "eval_duration": None,
        "total_duration": None,
        "load_duration": None,
    }
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
        "ranking_scores": [],
        "warnings": [],
    }
    parsed_command = parse_chat_command(request.message)

    log_event_fn(
        component="fastapi.chat.request",
        event="main_chat_request_received",
        trace_id=trace_id,
        endpoint="/chat",
        provider=provider,
        model=request.model,
        rag_enabled=use_rag,
        message_length=len(request.message),
        command=parsed_command.get("command") if isinstance(parsed_command, dict) else None,
    )

    try:
        if not isinstance(request.model, str) or not request.model.strip():
            raise HTTPException(
                status_code=400,
                detail={
                    "trace_id": trace_id,
                    "status": "error",
                    "code": "model_required",
                    "message": "El contrato de /chat requiere un model explicito.",
                    "retrieval_status": retrieval_status,
                    "chunk_ids": [],
                    "document_ids": [],
                    "source_filenames": [],
                    "query_original": context.get("query_original"),
                    "use_rag": use_rag,
                    "warnings": [],
                },
            )
        provider, model = resolve_provider_model_fn(provider, request.model)
        if parsed_command is not None:
            trace_source = "frontend"
            command = parsed_command["command"]
            tool_called = "create_document"
            use_rag = False
            context["retrieval_status"] = "DISABLED"
            command_response, command_metadata = _run_create_document_command(
                ask_chat_fn=ask_chat_fn,
                create_document_tool_fn=create_document_tool_fn,
                request=request,
                trace_id=trace_id,
                provider=provider,
                model=model,
                temperature=temperature,
                top_p=top_p,
                effective_max_tokens=effective_max_tokens,
            )
            status = "ok"
            retrieval_status = "DISABLED"
            answer_mode = command_response.answer_mode or "tool_result"
            final_answer = command_response.answer
            generation_latency_ms = command_metadata["generation_latency_ms"]
            tool_latency_ms = command_metadata["tool_latency_ms"]
            provider = command_metadata["provider"]
            model = command_metadata["model"]
            temperature = command_metadata["temperature"]
            effective_max_tokens = command_metadata["effective_max_tokens"]
            llm_metrics["tokens_input"] = command_metadata["tokens_input"]
            llm_metrics["tokens_output"] = command_metadata["tokens_output"]
            llm_metrics["tokens_total"] = command_metadata["tokens_total"]
            llm_metrics["prompt_eval_count"] = command_metadata["prompt_eval_count"]
            llm_metrics["eval_count"] = command_metadata["eval_count"]
            llm_metrics["prompt_eval_duration"] = command_metadata["prompt_eval_duration"]
            llm_metrics["eval_duration"] = command_metadata["eval_duration"]
            llm_metrics["total_duration"] = command_metadata["total_duration"]
            llm_metrics["load_duration"] = command_metadata["load_duration"]
            tool_called = command_response.tool_called
            tool_result_status = command_response.tool_result_status
            document_path = command_response.document_path
            document_filename = command_response.document_filename
            chars_written = command_response.chars_written
            overwrite_requested = command_response.overwrite_requested
            overwrite_applied = command_response.overwrite_applied
            overwrite_reason = command_response.overwrite_reason
            return command_response
        active_document_title = _normalize_active_document_title(request.active_document_title)
        use_active_context, active_context_reason = _should_use_active_context(
            query=request.message,
            active_document_id=request.active_document_id,
            active_document_title=active_document_title,
            active_corpus=request.active_corpus,
            last_source_intent=request.last_source_intent,
        )
        if use_rag:
            retrieval_started_at = time.perf_counter()
            top_k = request.top_k or 3
            if settings_obj.use_remote_rag:
                remote_rag_kwargs = {
                    "query": request.message,
                    "top_k": top_k,
                    "trace_id": trace_id,
                    "allowed_source_filenames": request.allowed_source_filenames,
                }
                if use_active_context and request.active_document_id is not None:
                    remote_rag_kwargs["active_document_id"] = request.active_document_id
                if use_active_context and active_document_title is not None:
                    remote_rag_kwargs["active_document_title"] = active_document_title
                if isinstance(request.active_corpus, str) and request.active_corpus.strip():
                    remote_rag_kwargs["active_corpus"] = request.active_corpus
                if isinstance(request.last_source_intent, str) and request.last_source_intent.strip():
                    remote_rag_kwargs["last_source_intent"] = request.last_source_intent
                context = query_remote_rag_fn(**remote_rag_kwargs)
            else:
                rag_kwargs = {
                    "limit": top_k,
                    "allowed_source_filenames": request.allowed_source_filenames,
                    "active_corpus": request.active_corpus,
                    "last_source_intent": request.last_source_intent,
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

        if use_rag and retrieval_status in MARKER_ONLY_RETRIEVAL_STATUSES:
            status = "ok"
            final_answer = _no_evidence_answer()
            answer_mode = ANSWER_MODE_SAFE_REFUSAL
            safe_refusal_response = _build_safe_refusal_chat_response(
                trace_id=trace_id,
                context=context,
                provider=provider,
                model=model,
                temperature=temperature,
                temperature_ignored=temperature_ignored,
                use_rag=True,
                latency_ms=int((time.perf_counter() - started_at) * 1000),
            )
            warnings = [item for item in safe_refusal_response.warnings if isinstance(item, str)]
            return safe_refusal_response

        llm_started_at = time.perf_counter()
        llm_message = context["prompt"]
        llm_use_rag = use_rag
        result = ask_chat_fn(
            message=llm_message,
            provider=provider,
            model=model,
            max_tokens=request.max_tokens,
            temperature=temperature,
            top_p=top_p,
            use_rag=llm_use_rag,
        )
        result["latency_ms"] = int((time.perf_counter() - llm_started_at) * 1000)
        generation_latency_ms += result["latency_ms"]
        llm_metrics["tokens_input"] = result.get("prompt_eval_count")
        llm_metrics["tokens_output"] = result.get("eval_count")
        llm_metrics["prompt_eval_count"] = result.get("prompt_eval_count")
        llm_metrics["eval_count"] = result.get("eval_count")
        llm_metrics["prompt_eval_duration"] = result.get("prompt_eval_duration")
        llm_metrics["eval_duration"] = result.get("eval_duration")
        llm_metrics["total_duration"] = result.get("total_duration")
        llm_metrics["load_duration"] = result.get("load_duration")
        # TODO: when the run schema can evolve safely, persist an explicit
        # observability_level to distinguish local runtime metrics from API-only providers.
        llm_metrics["tokens_total"] = (
            result.get("tokens_total")
            if isinstance(result.get("tokens_total"), (int, float))
            else None
        )
        if llm_metrics["tokens_total"] is None:
            prompt_eval_count = llm_metrics["tokens_input"]
            eval_count = llm_metrics["tokens_output"]
            if isinstance(prompt_eval_count, (int, float)) and isinstance(eval_count, (int, float)):
                llm_metrics["tokens_total"] = prompt_eval_count + eval_count
        response_provider = result.get("provider")
        if isinstance(response_provider, str) and response_provider.strip():
            provider = response_provider.strip().lower()
        model = result["model"]
        if isinstance(result.get("temperature"), (int, float)):
            temperature = float(result["temperature"])
        if isinstance(result.get("top_p"), (int, float)):
            top_p = float(result["top_p"])
        if isinstance(result.get("max_tokens"), int):
            effective_max_tokens = result["max_tokens"]
        if isinstance(result.get("temperature_ignored"), bool):
            temperature_ignored = result["temperature_ignored"]
        if isinstance(result.get("use_rag"), bool):
            use_rag = result["use_rag"]
        if temperature_ignored and "temperature_ignored_by_provider" not in warnings:
            warnings.append("temperature_ignored_by_provider")
        status = "ok"

        chunk_texts, chunk_ids, document_ids, source_filenames = _extract_chunk_response_data(context.get("chunks", [])) if use_rag else ([], [], [], [])
        context["chunk_ids"] = list(chunk_ids)
        context["document_ids"] = list(document_ids)
        context["source_filenames"] = list(source_filenames)
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
            final_answer = _no_evidence_answer()
            answer_mode = ANSWER_MODE_SAFE_REFUSAL
            safe_refusal_response = _build_safe_refusal_chat_response(
                trace_id=trace_id,
                context=context,
                provider=provider,
                model=model,
                temperature=temperature,
                temperature_ignored=temperature_ignored,
                use_rag=True,
                latency_ms=result["latency_ms"],
            )
            response_chunk_ids = list(safe_refusal_response.chunk_ids)
            warnings = [item for item in safe_refusal_response.warnings if isinstance(item, str)]
            return safe_refusal_response

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

        chat_response = ChatResponse(
            trace_id=trace_id,
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
            ranking_scores=context.get("ranking_scores", context.get("scores", [])),
            warnings=context.get("warnings", []),
        )
        final_answer = chat_response.answer
        warnings = [item for item in chat_response.warnings if isinstance(item, str)]
        response_chunk_ids = list(chat_response.chunk_ids)
        return chat_response

    except LLMClientError as exc:
        error_code = exc.code
        error_message = str(exc)
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
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, dict) else {}
        if isinstance(detail, dict):
            error_code = detail.get("code") if isinstance(detail.get("code"), str) else error_code
            error_message = detail.get("message") if isinstance(detail.get("message"), str) else error_message
            command = detail.get("command") if isinstance(detail.get("command"), str) else command
            tool_called = detail.get("tool_called") if isinstance(detail.get("tool_called"), str) else tool_called
            tool_result_status = (
                detail.get("tool_result_status")
                if isinstance(detail.get("tool_result_status"), str)
                else tool_result_status
            )
            document_path = detail.get("document_path") if isinstance(detail.get("document_path"), str) else document_path
            document_filename = (
                detail.get("document_filename")
                if isinstance(detail.get("document_filename"), str)
                else document_filename
            )
            detail_retrieval_status = detail.get("retrieval_status")
            if isinstance(detail_retrieval_status, str) and detail_retrieval_status.strip():
                retrieval_status = detail_retrieval_status
        raise
    except Exception as exc:
        error_code = "chat_internal_error"
        error_message = str(exc)
        raise HTTPException(
            status_code=500,
            detail={
                "trace_id": trace_id,
                "status": "error",
                "code": "chat_internal_error",
                "message": str(exc),
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
        trace_chunk_ids = response_chunk_ids or list(context.get("chunk_ids", []))
        evidence_used = _evidence_used_from_payload(
            chunk_ids=trace_chunk_ids,
            document_ids=context.get("document_ids", []),
            source_filenames=context.get("source_filenames", []),
        )
        fallback_used = _fallback_used_from_state(
            retrieval_status=retrieval_status,
            answer_mode=answer_mode,
            evidence_used=evidence_used,
        )
        fallback_reason = _fallback_reason_from_state(
            retrieval_status=retrieval_status,
            answer_mode=answer_mode,
            evidence_used=evidence_used,
        )
        trace_warnings = warnings or [item for item in context.get("warnings", []) if isinstance(item, str)]
        if temperature_ignored and "temperature_ignored_by_provider" not in trace_warnings:
            trace_warnings = [*trace_warnings, "temperature_ignored_by_provider"]
        trace_latency_ms = int((time.perf_counter() - started_at) * 1000)
        if persist_trace:
            try:
                _persist_chat_run(
                    save_chat_run_fn=save_chat_run_fn,
                    trace_id=trace_id,
                    request=request,
                    final_answer=final_answer,
                    provider=provider,
                    requested_model=requested_model,
                    model=model.strip() if isinstance(model, str) and model.strip() else None,
                    temperature=temperature,
                    max_tokens=effective_max_tokens,
                    top_p=top_p,
                    status=status,
                    retrieval_status=retrieval_status,
                    chunk_ids=trace_chunk_ids,
                    document_ids=context.get("document_ids", []),
                    source_filenames=context.get("source_filenames", []),
                    latency_ms=trace_latency_ms,
                    generation_latency_ms=generation_latency_ms or None,
                    retrieval_latency_ms=retrieval_latency_ms,
                    tool_latency_ms=tool_latency_ms,
                    error_code=error_code,
                    error_message=error_message,
                    warnings=trace_warnings,
                    use_rag=use_rag,
                    evidence_used=evidence_used,
                    fallback_used=fallback_used,
                    fallback_reason=fallback_reason,
                    answer_mode=answer_mode,
                    tokens_input=llm_metrics["tokens_input"],
                    tokens_output=llm_metrics["tokens_output"],
                    tokens_total=llm_metrics["tokens_total"],
                    prompt_eval_count=llm_metrics["prompt_eval_count"],
                    eval_count=llm_metrics["eval_count"],
                    prompt_eval_duration=llm_metrics["prompt_eval_duration"],
                    eval_duration=llm_metrics["eval_duration"],
                    total_duration=llm_metrics["total_duration"],
                    load_duration=llm_metrics["load_duration"],
                    trace_source=trace_source,
                    command=command,
                    tool_called=tool_called,
                    tool_result_status=tool_result_status,
                    document_path=document_path,
                    document_filename=document_filename,
                    chars_written=chars_written,
                    overwrite_requested=overwrite_requested,
                    overwrite_applied=overwrite_applied,
                    overwrite_reason=overwrite_reason,
                    source_intent=context.get("source_intent"),
                    selected_corpus=context.get("selected_corpus"),
                    active_document_id=context.get("active_document_id"),
                    active_document_title=context.get("active_document_title"),
                    active_context_used=bool(context.get("active_context_used")),
                    ranking_scores=context.get("ranking_scores", context.get("scores", [])),
                )
            except Exception as exc:
                log_event_fn(
                    component="fastapi.chat.trace",
                    event="fastapi.chat.trace.persist_failed",
                    trace_id=trace_id,
                    error_code="chat_trace_persist_failed",
                    error_message=str(exc),
                )
        log_event_fn(
            component="fastapi.chat",
            event="fastapi.chat.completed" if status == "ok" else "fastapi.chat.failed",
            trace_id=trace_id,
            endpoint="/chat",
            chat_id=request.chat_id,
            user_id=request.user_id,
            provider=provider,
            requested_model=requested_model,
            model=model,
            temperature=temperature,
            top_p=top_p,
            max_tokens=effective_max_tokens,
            temperature_ignored=temperature_ignored,
            use_rag=use_rag,
            status=status,
            latency_ms=trace_latency_ms,
            error_code=error_code,
            error_type=error_code,
            retrieval_status=retrieval_status,
            rag_enabled=use_rag,
            command=command,
            tool_called=tool_called,
            tool_result_status=tool_result_status,
            document_path=document_path,
            document_filename=document_filename,
            chars_written=chars_written,
            overwrite_requested=overwrite_requested,
            overwrite_applied=overwrite_applied,
            overwrite_reason=overwrite_reason,
            tool_latency_ms=tool_latency_ms,
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
            evidence_used=evidence_used,
            fallback_used=fallback_used,
            fallback_reason=fallback_reason,
            query_expansion_used=bool(context.get("query_expansion_used")),
            query_expansion_reason=context.get("query_expansion_reason"),
            expanded_query_terms=context.get("expanded_query_terms", []),
            candidate_filenames=context.get("candidate_filenames", []),
            selected_filenames=context.get("selected_filenames", []),
            chunk_ids=trace_chunk_ids,
            document_ids=context.get("document_ids", []),
            source_filenames=context.get("source_filenames", []),
            scores=context.get("scores", []),
            answer_mode=answer_mode,
            warnings=trace_warnings,
            final_message_preview=_message_preview(final_answer) if final_answer else "",
        )
