# FASTAPI

## Responsabilidad

Expone el contrato HTTP de chat y valida request/auth antes de entrar en el runtime.

## Entradas

- JSON `POST /chat`
- headers de auth

## Salidas

- `ChatResponse` en éxito
- `HTTPException.detail` en error

## Módulos relacionados

- `app/api/routes_chat.py`
- `app/api/runtime_bridge.py`
- `app/main.py`
- `app/schemas.py`

## Fallos posibles

- `422`
- `403`
- errores propagados desde runtime

## Relacionado

- [[POST_CHAT_FLOW]]
- [[CHAT_REQUEST]]
- [[CHAT_RESPONSE]]
- [[ROUTES_CHAT]]
