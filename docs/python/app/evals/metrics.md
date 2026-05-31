# app/evals/metrics.py

## Rol

Módulo de evaluación, carga de runs o cálculo de métricas.

## Identidad técnica

- Ruta real: `app/evals/metrics.py`
- Tipo: `eval`
- Ámbito: `backend principal`
- Módulo lógico: `app.evals.metrics`

## Símbolos principales

- Funciones: `_run_value`, `_normalized_text`, `safe_number`, `_derived_tokens_total`, `_tokens_per_second`, `_numbers`, `mean`, `safe_mean`, `safe_min`, `safe_max`, `stddev`, `safe_std`, `percentile`, `_failed_run`, `_error_rate`, `rate`, `_rate`, `_model_label`, `_operational_model_label`, `_operational_temperature_value`
- Funciones adicionales: `10` más.

## Dependencias internas directas

- [[python/app/evals/schemas|app/evals/schemas.py]]: importa `app.evals.schemas.ModelMetrics`, `app.evals.schemas.OperationalModelStats`, `app.evals.schemas.OperationalModelTemperatureStats`, `app.evals.schemas.RunRecord`, `app.evals.schemas.TimeSeriesPoint`.

## Dependencias inversas

- [[python/app/evals/__init__|app/evals/__init__.py]]: depende de este archivo vía `app.evals.metrics.build_model_operational_stats`, `app.evals.metrics.build_model_temperature_operational_stats`, `app.evals.metrics.build_timeseries`, `app.evals.metrics.compute_by_model`, `app.evals.metrics.compute_summary`.
- [[python/app/evals/router|app/evals/router.py]]: depende de este archivo vía `app.evals.metrics.build_model_operational_stats`, `app.evals.metrics.build_model_temperature_operational_stats`, `app.evals.metrics.build_timeseries`, `app.evals.metrics.compute_by_model`, `app.evals.metrics.compute_summary`.
- [[python/tests/test_runs_metrics|tests/test_runs_metrics.py]]: depende de este archivo vía `app.evals.metrics.compute_by_model`, `app.evals.metrics.compute_summary`, `app.evals.metrics.percentile`, `app.evals.metrics.safe_mean`.
- [[python/tests/test_runs_operational_stats|tests/test_runs_operational_stats.py]]: depende de este archivo vía `app.evals.metrics.build_model_operational_stats`, `app.evals.metrics.build_model_temperature_operational_stats`.

## Imports externos observados

- Paquetes o módulos externos detectados: `math`, `typing`

## Relación dentro del sistema

- Aporta trazabilidad, almacenamiento de ejecuciones o cálculo de métricas.

## Observaciones

- Sin observaciones adicionales relevantes a partir del análisis estático actual.

## Relacionado

- [[python/app/evals/INDEX]]
- [[OBSERVABILITY]]
- [[GLOSSARY]]
