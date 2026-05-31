# app/observability/chat_runs.py

## Rol

Módulo de observabilidad: logs, traces o persistencia de runs.

## Identidad técnica

- Ruta real: `app/observability/chat_runs.py`
- Tipo: `observability`
- Ámbito: `backend principal`
- Módulo lógico: `app.observability.chat_runs`

## Símbolos principales

- Clases: `ChatRunRecord`
- Funciones: `_utc_timestamp`, `_nullable_str`, `_nullable_number`, `_nullable_int`, `_nullable_temperature`, `_nullable_top_p`, `_normalized_generation_config`, `_int_list`, `_str_list`, `_warnings_list`, `_normalize_source`, `_normalize_endpoint`, `_normalize_retrieval_status`, `_normalize_tokens_total`, `_normalize_output_tokens_per_second`, `resolve_chat_runs_path`, `normalize_chat_run_record`, `_safe_trace_id`, `_timestamp_for_filename`, `_run_filename`
- Funciones adicionales: `8` más.

## Dependencias internas directas

- [[python/app/config|app/config.py]]: importa `app.config.settings`.
- [[python/app/observability/logging|app/observability/logging.py]]: importa `app.observability.logging.log_event`.
- [[python/app/schemas|app/schemas.py]]: importa `app.schemas.normalize_temperature`, `app.schemas.normalize_top_p`.

## Dependencias inversas

- [[python/app/chat_runs/store|app/chat_runs/store.py]]: depende de este archivo vía `app.observability.chat_runs.resolve_chat_runs_path`.
- [[python/app/chat_runtime|app/chat_runtime.py]]: depende de este archivo vía `app.observability.chat_runs.save_chat_run`.
- [[python/app/evals/loader|app/evals/loader.py]]: depende de este archivo vía `app.observability.chat_runs.resolve_chat_runs_path`.
- [[python/app/main|app/main.py]]: depende de este archivo vía `app.observability.chat_runs.clear_chat_runs`, `app.observability.chat_runs.list_chat_runs`, `app.observability.chat_runs.save_chat_run`.
- [[python/app/observability/__init__|app/observability/__init__.py]]: depende de este archivo vía `app.observability.chat_runs.ChatRunRecord`, `app.observability.chat_runs.DEFAULT_CHAT_RUNS_PATH`, `app.observability.chat_runs.clear_chat_runs`, `app.observability.chat_runs.get_chat_run`, `app.observability.chat_runs.list_chat_runs`, `app.observability.chat_runs.normalize_chat_run_record`, `app.observability.chat_runs.record_chat_run`, `app.observability.chat_runs.save_chat_run`, `app.observability.chat_runs.write_chat_run`.
- [[python/tests/test_chat_eval_foundation|tests/test_chat_eval_foundation.py]]: depende de este archivo vía `app.observability.chat_runs.write_chat_run`.
- [[python/tests/test_chat_runs_contract|tests/test_chat_runs_contract.py]]: depende de este archivo vía `app.observability.chat_runs.list_chat_runs`, `app.observability.chat_runs.save_chat_run`.

## Imports externos observados

- Paquetes o módulos externos detectados: `datetime`, `json`, `logging`, `os`, `pathlib`, `pydantic`, `re`, `typing`

## Relación dentro del sistema

- Aporta trazabilidad, almacenamiento de ejecuciones o cálculo de métricas.

## Observaciones

- Sin observaciones adicionales relevantes a partir del análisis estático actual.

## Relacionado

- [[python/app/observability/INDEX]]
- [[OBSERVABILITY]]
- [[GLOSSARY]]
