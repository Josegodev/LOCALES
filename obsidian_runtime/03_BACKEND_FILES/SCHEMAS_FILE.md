# app/schemas.py

## Ruta real

`app/schemas.py`

## Responsabilidad observada

Define `ChatRequest`, `ChatResponse` y normalizadores compartidos del contrato HTTP.

## Clases y funciones principales

- `ChatRequest`
- `ChatResponse`
- `normalize_temperature(...)`
- `normalize_top_p(...)`

## Quién lo llama

- `app/api/routes_chat.py`
- `app/chat/service.py`
- `app/chat_runtime.py`
- `app/observability/chat_runs.py`

## Entradas

- payloads HTTP y datos numéricos a normalizar

## Salidas

- modelos Pydantic y valores normalizados

## Riesgos

- `model` opcional en schema pero obligatorio en runtime
- el contrato de error no está cerrado aquí

## Relacionado

- [[CHAT_REQUEST]]
- [[CHAT_RESPONSE]]
- [[POST_CHAT_FLOW]]
