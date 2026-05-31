# OBSERVABILITY

## Responsabilidad

Genera `trace_id`, logs estructurados y persistencia de runs operativos.

## Entradas

- estado final del runtime
- métricas del proveedor
- evidencia RAG
- errores y warnings

## Salidas

- logs JSON
- runs persistidos
- datos recargables por stats y listados

## Módulos relacionados

- `app/observability/trace.py`
- `app/observability/logging.py`
- `app/observability/chat_runs.py`

## Fallos posibles

- persistencia fallida
- drift entre runs y traces
- asimetría métrica entre proveedores

## Relacionado

- [[TELEMETRY]]
- [[CHAT_RUNS_FILE]]
- [[LOGGING_FILE]]
- [[TRACE_FILE]]
