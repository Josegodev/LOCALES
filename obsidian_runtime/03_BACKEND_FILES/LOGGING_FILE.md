# app/observability/logging.py

## Ruta real

`app/observability/logging.py`

## Responsabilidad observada

Emite logs JSON estructurados del backend.

## Funciones principales

- `get_logger()`
- `log_event(...)`

## Quién lo llama

- `app/chat_runtime.py`
- `DB/chunks/document_context.py`
- `app/main.py`
- `app/observability/chat_runs.py`

## Salidas

- eventos JSON por stdout/logging

## Riesgos

- si cambia el shape del log, el debugging se vuelve menos consistente

## Relacionado

- [[OBSERVABILITY]]
- [[TELEMETRY]]
- [[CHAT_RUNTIME_FILE]]
