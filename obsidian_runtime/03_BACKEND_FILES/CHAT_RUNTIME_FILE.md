# app/chat_runtime.py

## Ruta real

`app/chat_runtime.py`

## Responsabilidad observada

Orquesta validación, RAG, generación, fallback, observabilidad y persistencia.

## Funciones principales

- `run_chat_request(...)`
- `_dependency_or_default(...)`
- `_persist_chat_run(...)`

## Quién lo llama

- `app/chat/service.py`

## A quién llama

- `app/llm_client.py`
- `app/rag_client.py`
- `DB/chunks/document_context.py`
- `app/observability/chat_runs.py`
- `app/observability/logging.py`
- `app/observability/trace.py`
- `app/tools/create_document.py`

## Entradas

- `ChatRequest`
- `ChatDependencies | None`

## Salidas

- `ChatResponse`
- `HTTPException` en error

## Efectos secundarios

- genera `trace_id`
- persiste runs
- emite logs

## Logs y métricas

- `latency_ms`
- `generation_latency_ms`
- `retrieval_latency_ms`
- `tokens_*`
- `prompt_eval_count`
- `eval_count`

## Riesgos

- módulo más acoplado del flujo
- mezcla contrato público, control de errores y persistencia

## Relacionado

- [[CHAT_RUNTIME]]
- [[POST_CHAT_FLOW]]
- [[ERROR_AND_FALLBACK_FLOW]]
