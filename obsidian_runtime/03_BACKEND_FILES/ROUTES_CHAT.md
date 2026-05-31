# app/api/routes_chat.py

## Ruta real

`app/api/routes_chat.py`

## Responsabilidad observada

Expone `POST /chat`, valida `ChatRequest` y exige acceso antes de delegar.

## Funciones principales

- `chat(...)`

## Quién lo llama

- FastAPI al resolver `POST /chat`

## A quién llama

- `app.api.runtime_bridge.main_module()`
- `app.auth.require_chat_access(...)`

## Entradas

- `ChatRequest`
- headers de auth

## Salidas

- `ChatResponse`
- errores HTTP propagados

## Efectos secundarios

- ninguno relevante fuera de auth y delegación

## Logs y métricas

- no genera métricas propias

## Riesgos

- depende del bridge dinámico hacia `app.main`
- el contrato de error no está modelado aquí

## Relacionado

- [[FASTAPI]]
- [[POST_CHAT_FLOW]]
- [[CHAT_REQUEST]]
