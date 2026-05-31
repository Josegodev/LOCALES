# rag_service/main.py

## Rol

Servicio FastAPI que expone retrieval remoto sobre la base documental.

## Identidad técnica

- Ruta real: `rag_service/main.py`
- Tipo: `rag_service`
- Ámbito: `servicio RAG remoto`
- Módulo lógico: `rag_service.main`

## Símbolos principales

- Clases: `RagQueryRequest`
- Funciones: `_sanitize_chunk`, `_no_evidence_response`, `_configure_documents_db_path`, `_normalize_retrieval_status`, `health`, `rag_health`, `rag_query`

## Dependencias internas directas

- [[python/DB/chunks/document_context|DB/chunks/document_context.py]]: importa `DB.chunks.document_context`, `DB.chunks.document_context.normalize_query`, `DB.chunks.document_context.normalize_terms`.
- [[python/app/config|app/config.py]]: importa `app.config.settings`.
- [[python/scripts/audit_documents_db|scripts/audit_documents_db.py]]: importa `scripts.audit_documents_db.audit_documents_db`.

## Dependencias inversas

- [[python/tests/test_remote_rag_service|tests/test_remote_rag_service.py]]: depende de este archivo vía `rag_service.main.app`.

## Imports externos observados

- Paquetes o módulos externos detectados: `fastapi`, `pathlib`, `pydantic`

## Relación dentro del sistema

- Su relación operativa exacta requiere contexto adicional del flujo donde se invoca.

## Observaciones

- Sin observaciones adicionales relevantes a partir del análisis estático actual.

## Relacionado

- [[python/rag_service/INDEX]]
- [[RAG_AND_EVIDENCE]]
- [[GLOSSARY]]
