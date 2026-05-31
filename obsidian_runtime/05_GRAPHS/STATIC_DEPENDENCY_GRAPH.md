# STATIC_DEPENDENCY_GRAPH

## Qué representa

Solo muestra relaciones estructurales por `import`.

## Dependencias clave

- `app/api/routes_chat.py -> app/api/runtime_bridge.py`
- `app/api/routes_chat.py -> app/schemas.py`
- `app/main.py -> app/chat/service.py`
- `app/main.py -> app/chat/dependencies.py`
- `app/chat_runtime.py -> app/llm_client.py`
- `app/chat_runtime.py -> app/rag_client.py`
- `app/chat_runtime.py -> DB/chunks/document_context.py`
- `app/chat_runtime.py -> app/observability/chat_runs.py`
- `app/llm_client.py -> app/adapters/ollama_client.py`
- `app/llm_client.py -> app/adapters/openai_client.py`

## Límite

No representa configuración, pruebas ni ramas de ejecución.

## Relacionado

- [[RUNTIME_GRAPH]]
- [[OBSERVED_TRACE_GRAPH]]
