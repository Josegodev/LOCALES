# app/api/runtime_bridge.py

## Ruta real

`app/api/runtime_bridge.py`

## Responsabilidad observada

Resuelve dinámicamente `app.main` para la capa HTTP.

## Funciones principales

- `main_module()`

## Quién lo llama

- `app/api/routes_chat.py`

## A quién llama

- `import_module("app.main")`

## Entradas

- ninguna entrada funcional externa

## Salidas

- módulo `app.main`

## Efectos secundarios

- import dinámico

## Riesgos

- menos explícito que un import estático

## Relacionado

- [[ROUTES_CHAT]]
- [[APP_MAIN]]
- [[POST_CHAT_FLOW]]
