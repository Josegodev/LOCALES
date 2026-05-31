# app/rag_client.py

## Rol

Archivo Python centrado en funciones utilitarias u operativas.

## Identidad técnica

- Ruta real: `app/rag_client.py`
- Tipo: `backend`
- Ámbito: `backend principal`
- Módulo lógico: `app.rag_client`

## Símbolos principales

- Funciones: `_controlled_no_evidence`, `query_remote_rag`

## Dependencias internas directas

- [[python/DB/chunks/document_context|DB/chunks/document_context.py]]: importa `DB.chunks.document_context.normalize_query`, `DB.chunks.document_context.normalize_terms`.
- [[python/app/config|app/config.py]]: importa `app.config.settings`.

## Dependencias inversas

- [[python/app/chat_runtime|app/chat_runtime.py]]: depende de este archivo vía `app.rag_client.query_remote_rag`.
- [[python/app/main|app/main.py]]: depende de este archivo vía `app.rag_client.query_remote_rag`.
- [[python/tests/test_rag_no_evidence_contract|tests/test_rag_no_evidence_contract.py]]: depende de este archivo vía `app.rag_client.NO_EVIDENCE_MARKER`, `app.rag_client.query_remote_rag`.
- [[python/tests/test_remote_rag_service|tests/test_remote_rag_service.py]]: depende de este archivo vía `app.rag_client`.

## Imports externos observados

- Paquetes o módulos externos detectados: `requests`

## Relación dentro del sistema

- Su relación operativa exacta requiere contexto adicional del flujo donde se invoca.

## Observaciones

- Sin observaciones adicionales relevantes a partir del análisis estático actual.

## Relacionado

- [[python/app/INDEX]]
- [[RUNTIME_FLOW]]
- [[GLOSSARY]]
