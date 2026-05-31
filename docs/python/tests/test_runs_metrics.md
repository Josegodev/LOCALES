# tests/test_runs_metrics.py

## Rol

Archivo de pruebas que valida contratos o regresiones del sistema.

## Identidad técnica

- Ruta real: `tests/test_runs_metrics.py`
- Tipo: `test`
- Ámbito: `suite de pruebas`
- Módulo lógico: `tests.test_runs_metrics`

## Símbolos principales

- Clases: `RunsMetricsTests`

## Dependencias internas directas

- [[python/app/evals/metrics|app/evals/metrics.py]]: importa `app.evals.metrics.compute_by_model`, `app.evals.metrics.compute_summary`, `app.evals.metrics.percentile`, `app.evals.metrics.safe_mean`.
- [[python/app/evals/schemas|app/evals/schemas.py]]: importa `app.evals.schemas.RunRecord`.

## Dependencias inversas

- No se han detectado dependencias internas inversas dentro del inventario analizado.

## Imports externos observados

- Paquetes o módulos externos detectados: `unittest`

## Relación dentro del sistema

- Participa en la validación automática del comportamiento del sistema.

## Observaciones

- La descripción funcional detallada se debe contrastar con el nombre del test y sus assertions.

## Relacionado

- [[python/tests/INDEX]]
- [[TECH_DEBT_AND_RISKS]]
- [[GLOSSARY]]
