# app/observability/logging.py

## Rol

Módulo de observabilidad: logs, traces o persistencia de runs.

## Identidad técnica

- Ruta real: `app/observability/logging.py`
- Tipo: `observability`
- Ámbito: `backend principal`
- Módulo lógico: `app.observability.logging`

## Símbolos principales

- Clases: `_StdoutProxy`, `JsonFormatter`
- Funciones: `get_logger`, `log_event`

## Dependencias internas directas

- No se han detectado imports internos directos del repositorio.

## Dependencias inversas

- [[python/DB/chunks/document_context|DB/chunks/document_context.py]]: depende de este archivo vía `app.observability.logging.log_event`.
- [[python/app/auth|app/auth.py]]: depende de este archivo vía `app.observability.logging.log_event`.
- [[python/app/chat_runs/store|app/chat_runs/store.py]]: depende de este archivo vía `app.observability.logging.log_event`.
- [[python/app/chat_runtime|app/chat_runtime.py]]: depende de este archivo vía `app.observability.logging.log_event`.
- [[python/app/evals/loader|app/evals/loader.py]]: depende de este archivo vía `app.observability.logging.log_event`.
- [[python/app/main|app/main.py]]: depende de este archivo vía `app.observability.logging.get_logger`, `app.observability.logging.log_event`.
- [[python/app/observability/__init__|app/observability/__init__.py]]: depende de este archivo vía `app.observability.logging.JsonFormatter`, `app.observability.logging.get_logger`, `app.observability.logging.log_event`.
- [[python/app/observability/chat_runs|app/observability/chat_runs.py]]: depende de este archivo vía `app.observability.logging.log_event`.
- [[python/app/observability/chat_trace|app/observability/chat_trace.py]]: depende de este archivo vía `app.observability.logging.log_event`.

## Imports externos observados

- Paquetes o módulos externos detectados: `json`, `logging`, `sys`, `typing`

## Relación dentro del sistema

- Aporta trazabilidad, almacenamiento de ejecuciones o cálculo de métricas.

## Observaciones

- Sin observaciones adicionales relevantes a partir del análisis estático actual.

## Relacionado

- [[python/app/observability/INDEX]]
- [[OBSERVABILITY]]
- [[GLOSSARY]]
