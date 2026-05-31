# DB/chunks/document_context.py

## Rol

Motor principal de RAG local sobre SQLite y ranking documental.

## Identidad técnica

- Ruta real: `DB/chunks/document_context.py`
- Tipo: `rag_local`
- Ámbito: `RAG local y base documental`
- Módulo lógico: `DB.chunks.document_context`

## Símbolos principales

- Clases: `DocumentsDbAudit`
- Funciones: `get_documents_db_path`, `_sqlite_uri_for_readonly`, `connect_documents_db_readonly`, `audit_documents_db`, `_warning_code_for_audit`, `_db_not_ready_trace`, `_log_rag_db_not_ready`, `normalize_query`, `normalize_terms`, `extract_quoted_terms`, `expand_query_terms`, `normalize_source_filenames`, `is_referential_query`, `source_intent_from_corpus_hint`, `classify_document_metadata`, `ensure_documents_metadata_schema`, `detect_source_intent`, `select_corpus_from_intent`, `_unique_filenames`, `_collect_trace`
- Funciones adicionales: `5` más.

## Dependencias internas directas

- [[python/app/config|app/config.py]]: importa `app.config.settings`.
- [[python/app/observability/logging|app/observability/logging.py]]: importa `app.observability.logging.log_event`.

## Dependencias inversas

- [[python/DB/chunks/ingest_pdf_markdown|DB/chunks/ingest_pdf_markdown.py]]: depende de este archivo vía `document_context.classify_document_metadata`, `document_context.ensure_documents_metadata_schema`.
- [[python/DB/chunks/run_ingest_pipeline|DB/chunks/run_ingest_pipeline.py]]: depende de este archivo vía `document_context.build_document_prompt`.
- [[python/DB/chunks/search_docs|DB/chunks/search_docs.py]]: depende de este archivo vía `document_context.search_chunks`.
- [[python/app/chat/retrieval|app/chat/retrieval.py]]: depende de este archivo vía `DB.chunks.document_context.detect_source_intent`, `DB.chunks.document_context.is_referential_query`, `DB.chunks.document_context.normalize_terms`, `DB.chunks.document_context.source_intent_from_corpus_hint`.
- [[python/app/chat_runtime|app/chat_runtime.py]]: depende de este archivo vía `DB.chunks.document_context.build_document_prompt`, `DB.chunks.document_context.detect_source_intent`, `DB.chunks.document_context.is_referential_query`, `DB.chunks.document_context.normalize_terms`, `DB.chunks.document_context.source_intent_from_corpus_hint`.
- [[python/app/main|app/main.py]]: depende de este archivo vía `DB.chunks.document_context.build_document_prompt`.
- [[python/app/rag_client|app/rag_client.py]]: depende de este archivo vía `DB.chunks.document_context.normalize_query`, `DB.chunks.document_context.normalize_terms`.
- [[python/rag_service/main|rag_service/main.py]]: depende de este archivo vía `DB.chunks.document_context`, `DB.chunks.document_context.normalize_query`, `DB.chunks.document_context.normalize_terms`.
- [[python/tests/test_document_context|tests/test_document_context.py]]: depende de este archivo vía `DB.chunks.document_context`.
- [[python/tests/test_retrieval_path_consistency|tests/test_retrieval_path_consistency.py]]: depende de este archivo vía `DB.chunks.document_context`.

## Imports externos observados

- Paquetes o módulos externos detectados: `dataclasses`, `pathlib`, `re`, `sqlite3`, `urllib`

## Relación dentro del sistema

- Está conectado con la cadena de recuperación documental y construcción de contexto RAG.

## Observaciones

- Sin observaciones adicionales relevantes a partir del análisis estático actual.

## Relacionado

- [[python/DB/chunks/INDEX]]
- [[RAG_AND_EVIDENCE]]
- [[GLOSSARY]]
