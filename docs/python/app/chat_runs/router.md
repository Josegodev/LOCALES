# app/chat_runs/router.py

## Rol

Módulo de consulta, almacenamiento o métricas de chat runs.

## Identidad técnica

- Ruta real: `app/chat_runs/router.py`
- Tipo: `chat_runs`
- Ámbito: `backend principal`
- Módulo lógico: `app.chat_runs.router`

## Símbolos principales

- Funciones: `_require_access`, `_normalized_filter_text`, `_apply_filters`, `list_chat_runs`, `chat_runs_stats`, `get_chat_run_by_trace_id`

## Dependencias internas directas

- [[python/app/auth|app/auth.py]]: importa `app.auth.bearer_scheme`, `app.auth.require_chat_access`.
- [[python/app/chat_runs/metrics|app/chat_runs/metrics.py]]: importa `app.chat_runs.metrics.summarize_runs`.
- [[python/app/chat_runs/store|app/chat_runs/store.py]]: importa `app.chat_runs.store.get_chat_run`, `app.chat_runs.store.load_chat_runs`.

## Dependencias inversas

- [[python/app/main|app/main.py]]: depende de este archivo vía `app.chat_runs.router.router`.

## Imports externos observados

- Paquetes o módulos externos detectados: `fastapi`, `typing`

## Relación dentro del sistema

- Aporta trazabilidad, almacenamiento de ejecuciones o cálculo de métricas.

## Observaciones

- Sin observaciones adicionales relevantes a partir del análisis estático actual.

## Relacionado

- [[python/app/chat_runs/INDEX]]
- [[OBSERVABILITY]]
- [[GLOSSARY]]
