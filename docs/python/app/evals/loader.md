# app/evals/loader.py

## Rol

Módulo de evaluación, carga de runs o cálculo de métricas.

## Identidad técnica

- Ruta real: `app/evals/loader.py`
- Tipo: `eval`
- Ámbito: `backend principal`
- Módulo lógico: `app.evals.loader`

## Símbolos principales

- Clases: `LoadedRuns`
- Funciones: `resolve_runs_dir`, `_nullable_str`, `_nullable_int`, `_nullable_float`, `_nullable_temperature`, `_normalize_retrieval_status`, `_tokens_total`, `_output_tokens_per_second`, `_sort_key`, `_is_incompatible_run_payload`, `_normalize_run`, `load_runs`

## Dependencias internas directas

- [[python/app/evals/schemas|app/evals/schemas.py]]: importa `app.evals.schemas.RunRecord`.
- [[python/app/observability/chat_runs|app/observability/chat_runs.py]]: importa `app.observability.chat_runs.resolve_chat_runs_path`.
- [[python/app/observability/logging|app/observability/logging.py]]: importa `app.observability.logging.log_event`.
- [[python/app/schemas|app/schemas.py]]: importa `app.schemas.normalize_temperature`.

## Dependencias inversas

- [[python/app/evals/__init__|app/evals/__init__.py]]: depende de este archivo vía `app.evals.loader.LoadedRuns`, `app.evals.loader.load_runs`, `app.evals.loader.resolve_runs_dir`.
- [[python/app/evals/router|app/evals/router.py]]: depende de este archivo vía `app.evals.loader.load_runs`.
- [[python/tests/test_runs_loader|tests/test_runs_loader.py]]: depende de este archivo vía `app.evals.loader.load_runs`.

## Imports externos observados

- Paquetes o módulos externos detectados: `dataclasses`, `datetime`, `json`, `logging`, `pathlib`, `typing`

## Relación dentro del sistema

- Aporta trazabilidad, almacenamiento de ejecuciones o cálculo de métricas.

## Observaciones

- Sin observaciones adicionales relevantes a partir del análisis estático actual.

## Relacionado

- [[python/app/evals/INDEX]]
- [[OBSERVABILITY]]
- [[GLOSSARY]]
