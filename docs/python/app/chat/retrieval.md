# app/chat/retrieval.py

## Rol

Módulo interno del runtime de chat extraído para reducir acoplamiento.

## Identidad técnica

- Ruta real: `app/chat/retrieval.py`
- Tipo: `chat_component`
- Ámbito: `backend principal`
- Módulo lógico: `app.chat.retrieval`

## Símbolos principales

- Clases: `RetrievalResult`
- Funciones: `_build_default_context`, `_normalize_no_evidence_retrieval_status`, `_extract_anchor_terms`, `_should_force_no_evidence`, `_normalize_active_document_title`, `_should_use_active_context`, `_normalize_source_filename`, `_extract_chunk_source_filename`, `_extract_chunk_response_data`, `retrieve_chat_context`

## Dependencias internas directas

- [[python/DB/chunks/document_context|DB/chunks/document_context.py]]: importa `DB.chunks.document_context.detect_source_intent`, `DB.chunks.document_context.is_referential_query`, `DB.chunks.document_context.normalize_terms`, `DB.chunks.document_context.source_intent_from_corpus_hint`.
- [[python/app/schemas|app/schemas.py]]: importa `app.schemas.ChatRequest`.

## Dependencias inversas

- [[python/app/chat/evidence|app/chat/evidence.py]]: depende de este archivo vía `app.chat.retrieval._extract_chunk_response_data`, `app.chat.retrieval._extract_chunk_source_filename`, `app.chat.retrieval._normalize_source_filename`.
- [[python/app/chat/fallback|app/chat/fallback.py]]: depende de este archivo vía `app.chat.retrieval.MARKER_ONLY_RETRIEVAL_STATUSES`, `app.chat.retrieval.NO_EVIDENCE_MARKER`.
- [[python/tests/test_chat_fallback|tests/test_chat_fallback.py]]: depende de este archivo vía `app.chat.retrieval.NO_EVIDENCE_MARKER`.
- [[python/tests/test_chat_retrieval|tests/test_chat_retrieval.py]]: depende de este archivo vía `app.chat.retrieval.NO_EVIDENCE_MARKER`, `app.chat.retrieval.retrieve_chat_context`.

## Imports externos observados

- Paquetes o módulos externos detectados: `dataclasses`, `pathlib`, `re`, `time`, `typing`

## Relación dentro del sistema

- Forma parte del runtime modularizado de chat.

## Observaciones

- Sin observaciones adicionales relevantes a partir del análisis estático actual.

## Relacionado

- [[python/app/chat/INDEX]]
- [[RUNTIME_FLOW]]
- [[GLOSSARY]]
