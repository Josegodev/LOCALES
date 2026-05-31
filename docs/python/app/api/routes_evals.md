# app/api/routes_evals.py

## Rol

Router FastAPI especializado en una superficie concreta de la API.

## Identidad técnica

- Ruta real: `app/api/routes_evals.py`
- Tipo: `router`
- Ámbito: `backend principal`
- Módulo lógico: `app.api.routes_evals`

## Símbolos principales

- Funciones: `_execute_chat_eval_case`, `chat_eval_runs`, `saved_chat_eval_runs`, `run_chat_eval_suite`

## Dependencias internas directas

- [[python/app/api/runtime_bridge|app/api/runtime_bridge.py]]: importa `app.api.runtime_bridge.main_module`.
- [[python/app/auth|app/auth.py]]: importa `app.auth.bearer_scheme`, `app.auth.require_chat_access`.
- [[python/app/schemas|app/schemas.py]]: importa `app.schemas.ChatEvalListResponse`, `app.schemas.ChatEvalRunResponse`, `app.schemas.ChatEvalRunsListResponse`, `app.schemas.ChatRequest`.

## Dependencias inversas

- [[python/app/api/__init__|app/api/__init__.py]]: depende de este archivo vía `app.api.routes_evals.router`.

## Imports externos observados

- Paquetes o módulos externos detectados: `fastapi`, `pydantic`

## Relación dentro del sistema

- Forma parte de la capa HTTP y expone contrato público o interno del backend.

## Observaciones

- Sin observaciones adicionales relevantes a partir del análisis estático actual.

## Relacionado

- [[python/app/api/INDEX]]
- [[RUNTIME_FLOW]]
- [[GLOSSARY]]
