# CHAT_RUNTIME

## Responsabilidad

Es el orquestador principal del flujo `POST /chat`.

## Entradas

- `ChatRequest`
- `ChatDependencies` o defaults del módulo

## Salidas

- `ChatResponse`
- errores HTTP controlados
- runs persistidos
- logs finales

## Módulos relacionados

- `app/chat_runtime.py`
- `app/llm_client.py`
- `app/rag_client.py`
- `DB/chunks/document_context.py`
- `app/observability/chat_runs.py`

## Fallos posibles

- `model_required`
- `invalid_provider_model_pair`
- provider timeout/unavailable
- RAG sin evidencia
- fallo de persistencia

## Relacionado

- [[POST_CHAT_FLOW]]
- [[RAG_BRANCH]]
- [[PROVIDER_BRANCH]]
- [[CHAT_RUNTIME_FILE]]
