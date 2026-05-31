# app/main.py

## Ruta real

`app/main.py`

## Responsabilidad observada

Ensamblador ASGI del backend y constructor de `ChatDependencies`.

## Símbolos principales

- `_build_chat_dependencies()`
- `_build_chat_service()`
- `run_chat_request(...)`

## Quién lo llama

- `app/api/runtime_bridge.py`
- tests que parchean `app.main.*`

## A quién llama

- `ChatService`
- `ChatDependencies`
- routers FastAPI

## Entradas

- `ChatRequest`

## Salidas

- `ChatResponse`

## Efectos secundarios

- configura CORS
- registra routers
- conecta funciones concretas al runtime

## Logs y métricas

- logs de arranque
- logs de CORS rechazado

## Riesgos

- punto de acoplamiento alto
- mantiene compatibilidad con tests legacy

## Relacionado

- [[FASTAPI]]
- [[CHAT_SERVICE_FILE]]
- [[CHAT_DEPENDENCIES_FILE]]
