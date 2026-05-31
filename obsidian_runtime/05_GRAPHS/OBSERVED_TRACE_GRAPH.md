# OBSERVED_TRACE_GRAPH

## Qué representa

Ruta observada por código y apoyada por tests del flujo principal.

## Camino observado

`frontend/app.js::sendChat -> frontend/api-client.js::fetchJson -> POST /chat -> app/api/routes_chat.py::chat -> app.main.run_chat_request -> ChatService.run_chat_request -> app/chat_runtime.py::run_chat_request -> RAG opcional -> app/llm_client.py::ask_chat -> adaptador proveedor -> ChatResponse -> save_chat_run/log_event -> frontend/app.js::renderChatResponse`

## Tests que refuerzan el camino

- `tests/test_frontend_api_client_static.py`
- `tests/test_chat_service.py`
- `tests/test_remote_rag_service.py`
- `tests/test_rag_no_evidence_contract.py`
- `tests/test_provider_model_resolution.py`

## Límite

No es una traza capturada en producción. Es una traza documental apoyada por comportamiento verificable.

## Relacionado

- [[RUNTIME_GRAPH]]
- [[UI_TO_RESPONSE]]
