# ERROR_AND_FALLBACK_FLOW

## Resumen

Esta nota documenta cómo fallan las cosas y dónde el runtime degrada de forma controlada.

## Fallos de entrada

- payload inválido -> `422`
- backend base URL inválida en UI -> error local en frontend
- auth rechazada -> `403`
- `model` ausente -> `400 model_required`

## Fallos `provider/model`

- combinación incoherente -> `400 invalid_provider_model_pair`
- modelo no disponible -> `404`
- API key OpenAI ausente o inválida -> `401`

## Fallos RAG

- RAG remoto no disponible -> degradación a `NO_EVIDENCE_FOR_ANSWER`
- RAG local sin evidencia -> `safe_refusal`
- `EVIDENCE_FOUND` inicial pero respuesta marker-only -> `safe_refusal`
- `RAG_ERROR` pendiente de confirmar como contrato público estable

## Fallos de proveedor

- Ollama caído -> `503`
- timeout proveedor -> `504`
- rate limit OpenAI -> `429`
- error HTTP proveedor -> `502` o mapeo específico

## CORS y conectividad

- preflight CORS rechazado -> `400` y log
- timeout frontend -> `request_timeout`
- red caída -> `network_error`

## Persistencia y observabilidad

- si falla `save_chat_run`, la respuesta puede salir igualmente
- el fallo de persistencia se registra como `chat_trace_persist_failed`

## Fallback observado

- `safe_refusal` cuando no hay evidencia suficiente
- `fallback_used=true`
- evidencia pública limpiada si no es fiable
- warning `temperature_ignored_by_provider` si OpenAI rechaza temperatura y el adaptador reintenta

## Relaciones verificadas

- `call`: `app/chat_runtime.py -> _build_safe_refusal_chat_response(...)`
- `call`: `app/chat_runtime.py -> save_chat_run(...)` en `finally`
- `call`: `frontend/app.js -> visibleChatErrorMessage(...)`
- `test`: `tests/test_rag_no_evidence_contract.py`, `tests/test_remote_rag_service.py`

## Relacionado

- [[DEBUG_CHAT_FAILURE]]
- [[DEBUG_RAG_FAILURE]]
- [[DEBUG_PROVIDER_FAILURE]]
- [[DEBUG_UI_BACKEND_FAILURE]]
- [[ERRORS]]
