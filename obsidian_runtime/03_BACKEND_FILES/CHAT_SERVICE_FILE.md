# app/chat/service.py

## Ruta real

`app/chat/service.py`

## Responsabilidad observada

Fachada mínima que pasa el request y las dependencias al runtime.

## Clases principales

- `ChatService`

## Quién lo llama

- `app/main.py`

## A quién llama

- `app.chat_runtime.run_chat_request(...)`

## Entradas

- `ChatRequest`
- `persist_trace`
- `ChatDependencies`

## Salidas

- `ChatResponse`

## Efectos secundarios

- ninguno propio

## Riesgos

- si cambia su firma, rompe tests de delegación

## Relacionado

- [[CHAT_SERVICE]]
- [[CHAT_RUNTIME_FILE]]
- [[CHAT_DEPENDENCIES_FILE]]
