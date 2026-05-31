# app/chat/fallback.py

## Rol

Módulo interno del runtime de chat extraído para reducir acoplamiento.

## Identidad técnica

- Ruta real: `app/chat/fallback.py`
- Tipo: `chat_component`
- Ámbito: `backend principal`
- Módulo lógico: `app.chat.fallback`

## Símbolos principales

- Funciones: `no_evidence_answer`, `normalize_no_evidence_retrieval_status`, `strip_no_evidence_markers`, `is_marker_only_no_evidence_answer`, `finalize_rag_answer`, `fallback_used_from_state`, `fallback_reason_from_state`, `no_evidence_warning_for_context`, `_clear_evidence_trace`, `clear_evidence_trace`, `build_safe_refusal_chat_response`

## Dependencias internas directas

- [[python/app/chat/response_builder|app/chat/response_builder.py]]: importa `app.chat.response_builder.build_chat_response`.
- [[python/app/chat/retrieval|app/chat/retrieval.py]]: importa `app.chat.retrieval.MARKER_ONLY_RETRIEVAL_STATUSES`, `app.chat.retrieval.NO_EVIDENCE_MARKER`.
- [[python/app/llm_errors|app/llm_errors.py]]: importa `app.llm_errors.LLMClientError`.

## Dependencias inversas

- [[python/app/chat_runtime|app/chat_runtime.py]]: depende de este archivo vía `app.chat.fallback.ACTIVE_CONTEXT_NO_EVIDENCE_WARNING`, `app.chat.fallback.ANSWER_MODE_DOCUMENTARY`, `app.chat.fallback.ANSWER_MODE_SAFE_REFUSAL`, `app.chat.fallback.ANSWER_MODE_STANDARD`, `app.chat.fallback.NO_EVIDENCE_EXPLANATION`, `app.chat.fallback.NO_EVIDENCE_WARNING`, `app.chat.fallback.clear_evidence_trace`, `app.chat.fallback.finalize_rag_answer`, `app.chat.fallback.is_marker_only_no_evidence_answer`, `app.chat.fallback.no_evidence_answer`, `app.chat.fallback.normalize_no_evidence_retrieval_status`, `app.chat.fallback.strip_no_evidence_markers`.
- [[python/tests/test_chat_fallback|tests/test_chat_fallback.py]]: depende de este archivo vía `app.chat.fallback.ANSWER_MODE_DOCUMENTARY`, `app.chat.fallback.ANSWER_MODE_SAFE_REFUSAL`, `app.chat.fallback.build_safe_refusal_chat_response`, `app.chat.fallback.fallback_reason_from_state`, `app.chat.fallback.fallback_used_from_state`, `app.chat.fallback.finalize_rag_answer`.

## Imports externos observados

- No se han detectado imports externos explícitos.

## Relación dentro del sistema

- Forma parte del runtime modularizado de chat.

## Observaciones

- Sin observaciones adicionales relevantes a partir del análisis estático actual.

## Relacionado

- [[python/app/chat/INDEX]]
- [[RUNTIME_FLOW]]
- [[GLOSSARY]]
