# app/chat_runtime.py

## Rol

Orquestador principal del flujo `POST /chat`.

## Identidad técnica

- Ruta real: `app/chat_runtime.py`
- Tipo: `backend`
- Ámbito: `backend principal`
- Módulo lógico: `app.chat_runtime`

## Símbolos principales

- Funciones: `_no_evidence_answer`, `_message_preview`, `parse_chat_command`, `_chat_trace_source`, `_strip_no_evidence_markers`, `_is_marker_only_no_evidence_answer`, `_normalize_no_evidence_retrieval_status`, `_clear_evidence_trace`, `_evidence_used_from_payload`, `_fallback_used_from_state`, `_fallback_reason_from_state`, `_no_evidence_warning_for_context`, `_build_safe_refusal_chat_response`, `_finalize_rag_answer`, `_extract_anchor_terms`, `_should_force_no_evidence`, `_normalize_active_document_title`, `_should_use_active_context`, `_normalize_source_filename`, `_extract_chunk_source_filename`
- Funciones adicionales: `6` más.

## Dependencias internas directas

- [[python/DB/chunks/document_context|DB/chunks/document_context.py]]: importa `DB.chunks.document_context.build_document_prompt`, `DB.chunks.document_context.detect_source_intent`, `DB.chunks.document_context.is_referential_query`, `DB.chunks.document_context.normalize_terms`, `DB.chunks.document_context.source_intent_from_corpus_hint`.
- [[python/app/chat/commands|app/chat/commands.py]]: importa `app.chat.commands.CREATE_DOCUMENT_COMMAND`, `app.chat.commands.CREATE_DOCUMENT_PREFIX`, `app.chat.commands.parse_chat_command`.
- [[python/app/chat/dependencies|app/chat/dependencies.py]]: importa `app.chat.dependencies.ChatDependencies`.
- [[python/app/chat/evidence|app/chat/evidence.py]]: importa `app.chat.evidence.evidence_used_from_payload`, `app.chat.evidence.extract_chunk_response_data`, `app.chat.evidence.extract_chunk_source_filename`, `app.chat.evidence.normalize_source_filename`.
- [[python/app/chat/fallback|app/chat/fallback.py]]: importa `app.chat.fallback.ACTIVE_CONTEXT_NO_EVIDENCE_WARNING`, `app.chat.fallback.ANSWER_MODE_DOCUMENTARY`, `app.chat.fallback.ANSWER_MODE_SAFE_REFUSAL`, `app.chat.fallback.ANSWER_MODE_STANDARD`, `app.chat.fallback.NO_EVIDENCE_EXPLANATION`, `app.chat.fallback.NO_EVIDENCE_WARNING`, `app.chat.fallback.clear_evidence_trace`, `app.chat.fallback.finalize_rag_answer`, `app.chat.fallback.is_marker_only_no_evidence_answer`, `app.chat.fallback.no_evidence_answer`, `app.chat.fallback.normalize_no_evidence_retrieval_status`, `app.chat.fallback.strip_no_evidence_markers`.
- [[python/app/config|app/config.py]]: importa `app.config.settings`.
- [[python/app/llm_client|app/llm_client.py]]: importa `app.llm_client.LLMClientError`, `app.llm_client.ask_chat`, `app.llm_client.resolve_provider_model`.
- [[python/app/observability/chat_runs|app/observability/chat_runs.py]]: importa `app.observability.chat_runs.save_chat_run`.
- [[python/app/observability/logging|app/observability/logging.py]]: importa `app.observability.logging.log_event`.
- [[python/app/observability/trace|app/observability/trace.py]]: importa `app.observability.trace.new_trace_id`.
- [[python/app/rag_client|app/rag_client.py]]: importa `app.rag_client.query_remote_rag`.
- [[python/app/schemas|app/schemas.py]]: importa `app.schemas.ChatRequest`, `app.schemas.ChatResponse`, `app.schemas.TEMPERATURE_DEFAULT`.
- [[python/app/tools/create_document|app/tools/create_document.py]]: importa `app.tools.create_document.CREATE_DOCUMENT_SYSTEM_PROMPT`, `app.tools.create_document.build_create_document_request`, `app.tools.create_document.create_document_tool`.

## Dependencias inversas

- [[python/app/chat/service|app/chat/service.py]]: depende de este archivo vía `app.chat_runtime`.

## Imports externos observados

- Paquetes o módulos externos detectados: `asyncio`, `datetime`, `fastapi`, `pathlib`, `re`, `time`, `typing`

## Relación dentro del sistema

- Es el núcleo del flujo de chat y coordina retrieval, generación, fallback y persistencia.

## Observaciones

- Es uno de los puntos con mayor acoplamiento interno del backend actual.

## Relacionado

- [[python/app/INDEX]]
- [[RUNTIME_FLOW]]
- [[GLOSSARY]]
