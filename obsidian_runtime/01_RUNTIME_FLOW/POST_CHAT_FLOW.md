# POST_CHAT_FLOW

## Punto de entrada

- endpoint: `POST /chat`
- router: `app/api/routes_chat.py`
- handler: `chat(...)`
- bridge: `app/api/runtime_bridge.py::main_module()`
- entrada backend visible: `app.main.run_chat_request(...)`
- runtime final: `app/chat_runtime.py::run_chat_request(...)`

## Schemas

- entrada: [[CHAT_REQUEST]]
- salida de éxito: [[CHAT_RESPONSE]]
- salida de error: [[ERRORS]]

## Validaciones

### Antes del runtime

- `ChatRequest` vía FastAPI/Pydantic
- auth vía `require_chat_access(...)`

### Dentro del runtime

- `model` explícito obligatorio
- `provider/model` compatible
- `use_rag` normalizado
- `trace_id` generado si no existe

## Delegación backend

1. `routes_chat.chat(...)`
2. `main_module().run_chat_request(request)`
3. `app.main.run_chat_request(...)`
4. `ChatService.run_chat_request(...)`
5. `app.chat_runtime.run_chat_request(...)`

## Ramas principales

### Rama `/creardoc`

- detecta comando en `app/chat_runtime.py`
- desactiva RAG
- llama al modelo
- llama a `app/tools/create_document.py`
- devuelve `ChatResponse` con metadatos de tool

### Rama chat normal sin RAG

- `retrieval_status="DISABLED"`
- llama directamente al LLM
- devuelve `standard_answer`

### Rama chat normal con RAG

- usa RAG local o remoto
- si no hay evidencia suficiente, devuelve `safe_refusal`
- si hay evidencia, llama al LLM con prompt enriquecido

## Errores principales

- `422` payload inválido
- `403` acceso rechazado
- `400 model_required`
- `400 invalid_provider_model_pair`
- `401 llm_auth_error`
- `404 llm_model_not_available`
- `429 llm_rate_limited`
- `503 llm_unavailable` o `llm_network_error`
- `504 llm_timeout`
- `500 chat_internal_error`

## Relaciones verificadas

- `import`: `app/api/routes_chat.py -> app.schemas`
- `call`: `app/api/routes_chat.py -> app.api.runtime_bridge.main_module()`
- `call`: `app.main.run_chat_request -> ChatService.run_chat_request`
- `call`: `ChatService.run_chat_request -> app.chat_runtime.run_chat_request`
- `test`: `tests/test_chat_service.py` confirma delegación del servicio

## Relacionado

- [[UI_TO_RESPONSE]]
- [[CHAT_REQUEST]]
- [[CHAT_RESPONSE]]
- [[ERRORS]]
- [[CHAT_RUNTIME_FILE]]
