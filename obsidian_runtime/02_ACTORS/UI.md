# UI

## Responsabilidad

Construye el payload, llama al backend y renderiza respuesta, warnings y evidencia.

## Entradas

- interacción del usuario
- `runtime-config.js`
- estado del formulario

## Salidas

- `POST /chat`
- `GET /health`
- `GET /api/models/chat`
- `GET /api/chat/options`
- render visual del `ChatResponse`

## Módulos relacionados

- `frontend/index.html`
- `frontend/app.js`
- `frontend/api-client.js`
- `frontend/runtime-config.js`

## Fallos posibles

- base URL inválida
- timeout del fetch
- red caída
- respuesta `422`, `401`, `403`, `500+`

## Evidencia

- `call`: `sendChat(...) -> fetchJsonWithLatency("/chat")`
- `test`: `tests/test_frontend_api_client_static.py`, `tests/test_frontend_create_document_static.py`

## Relacionado

- [[USER]]
- [[FASTAPI]]
- [[UI_TO_RESPONSE]]
- [[DEBUG_UI_BACKEND_FAILURE]]
