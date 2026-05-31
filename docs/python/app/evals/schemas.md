# app/evals/schemas.py

## Rol

Módulo de evaluación, carga de runs o cálculo de métricas.

## Identidad técnica

- Ruta real: `app/evals/schemas.py`
- Tipo: `eval`
- Ámbito: `backend principal`
- Módulo lógico: `app.evals.schemas`

## Símbolos principales

- Clases: `RunRecord`, `RunsListResponse`, `ModelMetrics`, `MetricsSummaryResponse`, `OperationalModelStats`, `OperationalModelTemperatureStats`, `OperationalStatsResponse`, `TimeSeriesPoint`, `TimeSeriesResponse`, `RunsByModelResponse`

## Dependencias internas directas

- No se han detectado imports internos directos del repositorio.

## Dependencias inversas

- [[python/app/evals/loader|app/evals/loader.py]]: depende de este archivo vía `app.evals.schemas.RunRecord`.
- [[python/app/evals/metrics|app/evals/metrics.py]]: depende de este archivo vía `app.evals.schemas.ModelMetrics`, `app.evals.schemas.OperationalModelStats`, `app.evals.schemas.OperationalModelTemperatureStats`, `app.evals.schemas.RunRecord`, `app.evals.schemas.TimeSeriesPoint`.
- [[python/app/evals/router|app/evals/router.py]]: depende de este archivo vía `app.evals.schemas.MetricsSummaryResponse`, `app.evals.schemas.ModelMetrics`, `app.evals.schemas.OperationalStatsResponse`, `app.evals.schemas.RunsByModelResponse`, `app.evals.schemas.RunsListResponse`, `app.evals.schemas.TimeSeriesResponse`.
- [[python/tests/test_runs_metrics|tests/test_runs_metrics.py]]: depende de este archivo vía `app.evals.schemas.RunRecord`.

## Imports externos observados

- Paquetes o módulos externos detectados: `pydantic`

## Relación dentro del sistema

- Aporta trazabilidad, almacenamiento de ejecuciones o cálculo de métricas.

## Observaciones

- Sin observaciones adicionales relevantes a partir del análisis estático actual.

## Relacionado

- [[python/app/evals/INDEX]]
- [[OBSERVABILITY]]
- [[GLOSSARY]]
