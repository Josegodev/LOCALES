# app/evals/__init__.py

## Rol

Inicializador del paquete y posible punto de reexportación.

## Identidad técnica

- Ruta real: `app/evals/__init__.py`
- Tipo: `eval`
- Ámbito: `backend principal`
- Módulo lógico: `app.evals`

## Símbolos principales

- No expone clases o funciones top-level; puede actuar como paquete o marcador.

## Dependencias internas directas

- [[python/app/evals/loader|app/evals/loader.py]]: importa `app.evals.loader.LoadedRuns`, `app.evals.loader.load_runs`, `app.evals.loader.resolve_runs_dir`.
- [[python/app/evals/metrics|app/evals/metrics.py]]: importa `app.evals.metrics.build_model_operational_stats`, `app.evals.metrics.build_model_temperature_operational_stats`, `app.evals.metrics.build_timeseries`, `app.evals.metrics.compute_by_model`, `app.evals.metrics.compute_summary`.

## Dependencias inversas

- No se han detectado dependencias internas inversas dentro del inventario analizado.

## Imports externos observados

- No se han detectado imports externos explícitos.

## Relación dentro del sistema

- Aporta trazabilidad, almacenamiento de ejecuciones o cálculo de métricas.

## Observaciones

- Archivo especial de paquete; suele concentrar reexports o inicialización mínima.

## Relacionado

- [[python/app/evals/INDEX]]
- [[OBSERVABILITY]]
- [[GLOSSARY]]
