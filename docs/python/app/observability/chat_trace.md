# app/observability/chat_trace.py

## Rol

Módulo de observabilidad: logs, traces o persistencia de runs.

## Identidad técnica

- Ruta real: `app/observability/chat_trace.py`
- Tipo: `observability`
- Ámbito: `backend principal`
- Módulo lógico: `app.observability.chat_trace`

## Símbolos principales

- Clases: `ChatTraceRecord`
- Funciones: `_utc_timestamp`, `_nullable_str`, `_nullable_number`, `_int_list`, `_str_list`, `_warnings_list`, `_normalize_source`, `_normalize_endpoint`, `_normalize_retrieval_status`, `_normalize_tokens_total`, `_trace_path`, `normalize_chat_trace_record`, `record_chat_trace`, `_load_jsonl_chat_traces`, `list_chat_traces`, `clear_chat_traces`, `write_chat_trace`

## Dependencias internas directas

- [[python/app/config|app/config.py]]: importa `app.config.settings`.
- [[python/app/observability/logging|app/observability/logging.py]]: importa `app.observability.logging.log_event`.

## Dependencias inversas

- [[python/app/observability/__init__|app/observability/__init__.py]]: depende de este archivo vía `app.observability.chat_trace.ChatTraceRecord`, `app.observability.chat_trace.DEFAULT_CHAT_TRACE_PATH`, `app.observability.chat_trace.clear_chat_traces`, `app.observability.chat_trace.list_chat_traces`, `app.observability.chat_trace.normalize_chat_trace_record`, `app.observability.chat_trace.record_chat_trace`, `app.observability.chat_trace.write_chat_trace`.

## Imports externos observados

- Paquetes o módulos externos detectados: `datetime`, `json`, `logging`, `pathlib`, `pydantic`, `typing`

## Relación dentro del sistema

- Aporta trazabilidad, almacenamiento de ejecuciones o cálculo de métricas.

## Observaciones

- Convive con otras rutas de persistencia de runs/traces; revisar posibles zonas de drift.

## Relacionado

- [[python/app/observability/INDEX]]
- [[OBSERVABILITY]]
- [[GLOSSARY]]
