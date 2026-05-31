# app/observability/chat_runs.py

## Ruta real

`app/observability/chat_runs.py`

## Responsabilidad observada

Normaliza y persiste runs operativos del chat.

## Funciones principales

- `resolve_chat_runs_path(...)`
- `save_chat_run(...)`
- `list_chat_runs(...)`

## Quién lo llama

- `app/chat_runtime.py`
- `app/main.py`
- cargadores de runs y evals

## A quién llama

- filesystem en `CHAT_RUNS/`
- logging estructurado

## Entradas

- payload del run final

## Salidas

- archivo JSON por run

## Riesgos

- drift con `chat_trace.py`
- configuración ambigua `CHAT_RUNS_PATH`

## Relacionado

- [[OBSERVABILITY]]
- [[TELEMETRY]]
- [[DEBUG_CHAT_FAILURE]]
