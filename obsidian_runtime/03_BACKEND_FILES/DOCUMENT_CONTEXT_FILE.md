# DB/chunks/document_context.py

## Ruta real

`DB/chunks/document_context.py`

## Responsabilidad observada

Motor RAG local sobre SQLite y constructor de prompts documentales.

## Funciones principales

- `build_document_prompt(...)`
- `normalize_query(...)`
- `normalize_terms(...)`
- `detect_source_intent(...)`

## Quién lo llama

- `app/chat_runtime.py`
- `rag_service/main.py`
- `app/rag_client.py` para normalización

## A quién llama

- SQLite
- logging estructurado

## Entradas

- query
- top_k / limit
- filtros y contexto activo

## Salidas

- `prompt`
- `chunks`
- `chunk_ids`
- `source_filenames`
- `retrieval_status`

## Riesgos

- drift de corpus
- evidencia insuficiente
- dependencia fuerte del esquema SQLite

## Relacionado

- [[RAG_BRANCH]]
- [[RAG_EVIDENCE]]
- [[RAG_SERVICE_MAIN_FILE]]
