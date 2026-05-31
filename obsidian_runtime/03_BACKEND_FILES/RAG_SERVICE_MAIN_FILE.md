# rag_service/main.py

## Ruta real

`rag_service/main.py`

## Responsabilidad observada

Expone retrieval remoto reutilizando el mismo motor documental local.

## Funciones principales

- `rag_query(...)`
- `rag_health()`

## Quién lo llama

- `app/rag_client.py`
- tests del servicio RAG

## A quién llama

- `DB/chunks/document_context.build_document_prompt(...)`

## Entradas

- `query`
- `top_k`
- `trace_id`
- filtros de documento/corpus

## Salidas

- payload JSON de retrieval

## Riesgos

- no es un motor independiente; comparte drift del RAG local

## Relacionado

- [[RAG_CLIENT_FILE]]
- [[RAG_BRANCH]]
- [[OBSERVED_TRACE_GRAPH]]
