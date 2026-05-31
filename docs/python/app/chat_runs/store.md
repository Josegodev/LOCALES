# app/chat_runs/store.py

## Rol

Módulo de consulta, almacenamiento o métricas de chat runs.

## Identidad técnica

- Ruta real: `app/chat_runs/store.py`
- Tipo: `chat_runs`
- Ámbito: `backend principal`
- Módulo lógico: `app.chat_runs.store`

## Símbolos principales

- Clases: `LoadedChatRuns`
- Funciones: `resolve_runs_dir`, `_nullable_str`, `_nullable_bool`, `_safe_number`, `_nullable_temperature`, `_int_list`, `_str_list`, `_normalized_tokens_total`, `_normalized_output_tokens_per_second`, `_normalized_retrieval_status`, `_infer_observability_level`, `_is_incompatible_payload`, `normalize_run`, `_sort_key`, `load_chat_runs`, `get_chat_run`

## Dependencias internas directas

- [[python/app/observability/chat_runs|app/observability/chat_runs.py]]: importa `app.observability.chat_runs.resolve_chat_runs_path`.
- [[python/app/observability/logging|app/observability/logging.py]]: importa `app.observability.logging.log_event`.
- [[python/app/schemas|app/schemas.py]]: importa `app.schemas.normalize_temperature`.

## Dependencias inversas

- [[python/app/chat_runs/router|app/chat_runs/router.py]]: depende de este archivo vía `app.chat_runs.store.get_chat_run`, `app.chat_runs.store.load_chat_runs`.
- [[python/tests/test_chat_runs_store|tests/test_chat_runs_store.py]]: depende de este archivo vía `app.chat_runs.store.get_chat_run`, `app.chat_runs.store.load_chat_runs`.

## Imports externos observados

- Paquetes o módulos externos detectados: `dataclasses`, `datetime`, `json`, `logging`, `math`, `pathlib`, `typing`

## Relación dentro del sistema

- Aporta trazabilidad, almacenamiento de ejecuciones o cálculo de métricas.

## Observaciones

- Sin observaciones adicionales relevantes a partir del análisis estático actual.

## Relacionado

- [[python/app/chat_runs/INDEX]]
- [[OBSERVABILITY]]
- [[GLOSSARY]]
