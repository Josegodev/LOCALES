# Contratos HTTP

## Endpoints detectados
- `app.get('/health')` en `DB/api_server.py:128` funcion `health`
- `app.get('/profiles')` en `DB/api_server.py:138` funcion `get_profiles`
- `app.post('/profiles')` en `DB/api_server.py:145` funcion `create_profile`
- `app.get('/profiles/{slug}')` en `DB/api_server.py:186` funcion `get_profile`
- `app.get('/profiles/{slug}/stats')` en `DB/api_server.py:195` funcion `get_profile_stats`
- `app.get('/profiles/{slug}/memory')` en `DB/api_server.py:207` funcion `get_profile_memory`
- `app.post('/profiles/{slug}/memory/approve')` en `DB/api_server.py:225` funcion `approve_profile_memory`
- `app.post('/chat')` en `DB/api_server.py:248` funcion `chat`
- `app.post('/profiles/{slug}/prune')` en `DB/api_server.py:339` funcion `prune_profile`
- `app.post('/profiles/{slug}/memory/enforce-limit')` en `DB/api_server.py:353` funcion `enforce_profile_memory_limit`
- `app.get('/health')` en `DB/chunks/api.py:36` funcion `health`
- `app.post('/document-chat', response_model=DocumentChatResponse)` en `DB/chunks/api.py:41` funcion `document_chat`
- `app.get('/health')` en `app/main.py:15` funcion `health`
- `app.post('/documents', response_model=DocumentCreateResponse)` en `app/main.py:20` funcion `create_document_endpoint`
- `app.post('/chat', response_model=ChatResponse)` en `app/main.py:46` funcion `chat`
- `app.post('/rag/query')` en `llm_lab/api.py:28` funcion `rag_query`
- `app.post('/model/proposal')` en `llm_lab/api.py:53` funcion `model_proposal`
- `app.post('/model/answer')` en `llm_lab/api.py:61` funcion `model_answer`
- `app.post('/eval/run')` en `llm_lab/api.py:69` funcion `eval_run`
- `app.post('/v1/chat/completions')` en `llm_lab/continue_server.py:25` funcion `chat_completions`

## Contratos principales
### `app/main.py`
- `GET /health` -> `{"status":"ok"}`.
- `POST /documents` usa `DocumentCreateRequest`: `filename`, `content`, `overwrite`. Devuelve `DocumentCreateResponse`.
- `POST /chat` usa `ChatRequest`: `message`, `model`, `max_tokens`, `temperature`, `top_k`. Devuelve `ChatResponse` declarado con `status`, `model`, `answer`, `latency_ms`.
- AMBIGUO: el handler envia tambien `retrieval_status` y `chunks`, no presentes en `ChatResponse`.

### `DB/api_server.py`
- `POST /chat` usa `slug`, `prompt`, `memory_limit`; guarda raw prompt/output y devuelve `content`.
- `POST /profiles` crea perfil con `slug`, `model_name`, parametros y limites de retencion.
- Endpoints `/profiles/{slug}/...` gestionan stats, memoria, pruning y limites.

### `DB/chunks/api.py`
- `POST /document-chat` usa `query` y `top_k`; devuelve `status`, `query`, `chunks`, `answer`.

### `llm_lab/api.py`
- `/rag/query`: `query`, `top_k`; escribe traza en `llm_lab/artifacts`.
- `/model/proposal`: `task`, `context`, `model_id`; valida salida como contrato de propuesta.
- `/model/answer`: `question`, `context`, `model_id`; valida salida como contrato de respuesta.
- `/eval/run`: ejecuta casos de `llm_lab/eval/eval_cases.json`.

## Riesgos de contrato
- CRITICO: dos contratos `/chat` incompatibles (`message` vs `slug/prompt`).
- CRITICO: `run_telegram.py:ask_backend()` contiene el contrato `slug/prompt` contra `app/main.py`, pero no se usa en el flujo normal.
- INFORMATIVO: `llm_lab/continue_server.py` imita `/v1/chat/completions`, pero no soporta streaming.
