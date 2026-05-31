# app/evals/router.py

## Rol

Módulo de evaluación, carga de runs o cálculo de métricas.

## Identidad técnica

- Ruta real: `app/evals/router.py`
- Tipo: `eval`
- Ámbito: `backend principal`
- Módulo lógico: `app.evals.router`

## Símbolos principales

- Funciones: `_require_access`, `list_runs`, `runs_summary`, `runs_timeseries`, `runs_operational_stats`, `runs_by_model`

## Dependencias internas directas

- [[python/app/auth|app/auth.py]]: importa `app.auth.bearer_scheme`, `app.auth.require_chat_access`.
- [[python/app/config|app/config.py]]: importa `app.config.settings`.
- [[python/app/evals/loader|app/evals/loader.py]]: importa `app.evals.loader.load_runs`.
- [[python/app/evals/metrics|app/evals/metrics.py]]: importa `app.evals.metrics.build_model_operational_stats`, `app.evals.metrics.build_model_temperature_operational_stats`, `app.evals.metrics.build_timeseries`, `app.evals.metrics.compute_by_model`, `app.evals.metrics.compute_summary`.
- [[python/app/evals/schemas|app/evals/schemas.py]]: importa `app.evals.schemas.MetricsSummaryResponse`, `app.evals.schemas.ModelMetrics`, `app.evals.schemas.OperationalStatsResponse`, `app.evals.schemas.RunsByModelResponse`, `app.evals.schemas.RunsListResponse`, `app.evals.schemas.TimeSeriesResponse`.

## Dependencias inversas

- [[python/app/main|app/main.py]]: depende de este archivo vía `app.evals.router.router`.

## Imports externos observados

- Paquetes o módulos externos detectados: `fastapi`

## Relación dentro del sistema

- Aporta trazabilidad, almacenamiento de ejecuciones o cálculo de métricas.

## Observaciones

- Sin observaciones adicionales relevantes a partir del análisis estático actual.

## Relacionado

- [[python/app/evals/INDEX]]
- [[OBSERVABILITY]]
- [[GLOSSARY]]
