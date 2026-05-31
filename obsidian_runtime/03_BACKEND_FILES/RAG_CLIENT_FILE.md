# app/rag_client.py

## Ruta real

`app/rag_client.py`

## Responsabilidad observada

Consume el servicio RAG remoto y degrada a `NO_EVIDENCE_FOR_ANSWER` si el servicio falla.

## Funciones principales

- `query_remote_rag(...)`

## Quién lo llama

- `app/chat_runtime.py`

## A quién llama

- `POST /rag/query`

## Entradas

- `query`
- `top_k`
- `trace_id`
- filtros de documento/corpus

## Salidas

- payload de retrieval

## Efectos secundarios

- red hacia el servicio RAG

## Riesgos

- respuesta remota inválida
- timeout o conexión caída

## Relacionado

- [[RAG]]
- [[RAG_BRANCH]]
- [[RAG_SERVICE_MAIN_FILE]]
