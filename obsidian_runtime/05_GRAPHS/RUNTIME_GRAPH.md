# RUNTIME_GRAPH

## Qué representa

Este grafo resume el camino operativo principal de una petición de chat.

## Mermaid

```mermaid
flowchart LR
    U[Usuario] --> UI[frontend/app.js]
    UI --> API[frontend/api-client.js]
    API --> CHAT[POST /chat]
    CHAT --> ROUTE[app/api/routes_chat.py]
    ROUTE --> BRIDGE[app/api/runtime_bridge.py]
    BRIDGE --> MAIN[app/main.py]
    MAIN --> SERVICE[app/chat/service.py]
    SERVICE --> RUNTIME[app/chat_runtime.py]
    RUNTIME -->|use_rag=false| LLM[app/llm_client.py]
    RUNTIME -->|RAG local| LOCAL[DB/chunks/document_context.py]
    RUNTIME -->|RAG remoto| REMOTE[app/rag_client.py]
    REMOTE --> RAGSVC[rag_service/main.py]
    LOCAL --> LLM
    RAGSVC --> LLM
    LLM --> OLLAMA[app/adapters/ollama_client.py]
    LLM --> OPENAI[app/adapters/openai_client.py]
    RUNTIME --> OBS[app/observability/*]
    OBS --> UI
```

## Fuente estructural

La base más completa está sintetizada en `docs/runtime_graph.json`.

## Relacionado

- [[STATIC_DEPENDENCY_GRAPH]]
- [[OBSERVED_TRACE_GRAPH]]
- [[UI_TO_RESPONSE]]
