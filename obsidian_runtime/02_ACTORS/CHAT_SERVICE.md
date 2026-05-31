# CHAT_SERVICE

## Responsabilidad

Envuelve el runtime y le pasa dependencias explícitas.

## Entradas

- `ChatRequest`
- `persist_trace`
- `ChatDependencies`

## Salidas

- `ChatResponse`

## Módulos relacionados

- `app/chat/service.py`
- `app/chat/dependencies.py`
- `app/chat_runtime.py`

## Fallos posibles

- hereda los fallos del runtime
- puede divergir si cambian dependencias inyectadas

## Evidencia

- `call`: `ChatService.run_chat_request -> app.chat_runtime.run_chat_request`
- `test`: `tests/test_chat_service.py`

## Relacionado

- [[CHAT_RUNTIME]]
- [[POST_CHAT_FLOW]]
- [[CHAT_SERVICE_FILE]]
