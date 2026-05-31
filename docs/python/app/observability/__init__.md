# app/observability/__init__.py

## Rol

Inicializador del paquete y posible punto de reexportación.

## Identidad técnica

- Ruta real: `app/observability/__init__.py`
- Tipo: `observability`
- Ámbito: `backend principal`
- Módulo lógico: `app.observability`

## Símbolos principales

- No expone clases o funciones top-level; puede actuar como paquete o marcador.

## Dependencias internas directas

- [[python/app/observability/chat_runs|app/observability/chat_runs.py]]: importa `app.observability.chat_runs.ChatRunRecord`, `app.observability.chat_runs.DEFAULT_CHAT_RUNS_PATH`, `app.observability.chat_runs.clear_chat_runs`, `app.observability.chat_runs.get_chat_run`, `app.observability.chat_runs.list_chat_runs`, `app.observability.chat_runs.normalize_chat_run_record`, `app.observability.chat_runs.record_chat_run`, `app.observability.chat_runs.save_chat_run`, `app.observability.chat_runs.write_chat_run`.
- [[python/app/observability/chat_trace|app/observability/chat_trace.py]]: importa `app.observability.chat_trace.ChatTraceRecord`, `app.observability.chat_trace.DEFAULT_CHAT_TRACE_PATH`, `app.observability.chat_trace.clear_chat_traces`, `app.observability.chat_trace.list_chat_traces`, `app.observability.chat_trace.normalize_chat_trace_record`, `app.observability.chat_trace.record_chat_trace`, `app.observability.chat_trace.write_chat_trace`.
- [[python/app/observability/logging|app/observability/logging.py]]: importa `app.observability.logging.JsonFormatter`, `app.observability.logging.get_logger`, `app.observability.logging.log_event`.
- [[python/app/observability/trace|app/observability/trace.py]]: importa `app.observability.trace.new_trace_id`.

## Dependencias inversas

- No se han detectado dependencias internas inversas dentro del inventario analizado.

## Imports externos observados

- No se han detectado imports externos explícitos.

## Relación dentro del sistema

- Aporta trazabilidad, almacenamiento de ejecuciones o cálculo de métricas.

## Observaciones

- Archivo especial de paquete; suele concentrar reexports o inicialización mínima.

## Relacionado

- [[python/app/observability/INDEX]]
- [[OBSERVABILITY]]
- [[GLOSSARY]]
