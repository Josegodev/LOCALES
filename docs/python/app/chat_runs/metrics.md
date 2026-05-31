# app/chat_runs/metrics.py

## Rol

Módulo de consulta, almacenamiento o métricas de chat runs.

## Identidad técnica

- Ruta real: `app/chat_runs/metrics.py`
- Tipo: `chat_runs`
- Ámbito: `backend principal`
- Módulo lógico: `app.chat_runs.metrics`

## Símbolos principales

- Funciones: `_safe_number`, `_normalized_text`, `_is_ok_run`, `_is_error_run`, `_rate`, `_mean`, `_label`, `percentile`, `_summarize_group`, `group_by_model`, `group_by_provider`, `summarize_runs`

## Dependencias internas directas

- No se han detectado imports internos directos del repositorio.

## Dependencias inversas

- [[python/app/chat_runs/router|app/chat_runs/router.py]]: depende de este archivo vía `app.chat_runs.metrics.summarize_runs`.
- [[python/tests/test_chat_runs_metrics|tests/test_chat_runs_metrics.py]]: depende de este archivo vía `app.chat_runs.metrics.group_by_model`, `app.chat_runs.metrics.group_by_provider`, `app.chat_runs.metrics.percentile`, `app.chat_runs.metrics.summarize_runs`.

## Imports externos observados

- Paquetes o módulos externos detectados: `math`, `typing`

## Relación dentro del sistema

- Aporta trazabilidad, almacenamiento de ejecuciones o cálculo de métricas.

## Observaciones

- Sin observaciones adicionales relevantes a partir del análisis estático actual.

## Relacionado

- [[python/app/chat_runs/INDEX]]
- [[OBSERVABILITY]]
- [[GLOSSARY]]
