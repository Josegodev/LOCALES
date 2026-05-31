# app/observability/trace.py

## Ruta real

`app/observability/trace.py`

## Responsabilidad observada

Genera `trace_id` para correlación.

## Funciones principales

- `new_trace_id()`

## Quién lo llama

- `app/chat_runtime.py`
- `app/main.py`

## Salidas

- UUID en formato hex por defecto

## Riesgos

- si cambia el formato, afecta correlación UI/backend/runs

## Relacionado

- [[OBSERVABILITY]]
- [[TELEMETRY]]
- [[CHAT_RUNTIME_FILE]]
