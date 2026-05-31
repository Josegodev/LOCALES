# app/api/routes_chat_runs.py

## Rol

Router FastAPI especializado en una superficie concreta de la API.

## Identidad técnica

- Ruta real: `app/api/routes_chat_runs.py`
- Tipo: `router`
- Ámbito: `backend principal`
- Módulo lógico: `app.api.routes_chat_runs`

## Símbolos principales

- Funciones: `chat_runs`

## Dependencias internas directas

- [[python/app/api/runtime_bridge|app/api/runtime_bridge.py]]: importa `app.api.runtime_bridge.main_module`.
- [[python/app/auth|app/auth.py]]: importa `app.auth.bearer_scheme`, `app.auth.require_chat_access`.
- [[python/app/schemas|app/schemas.py]]: importa `app.schemas.ChatRunListResponse`.

## Dependencias inversas

- [[python/app/api/__init__|app/api/__init__.py]]: depende de este archivo vía `app.api.routes_chat_runs.router`.

## Imports externos observados

- Paquetes o módulos externos detectados: `fastapi`

## Relación dentro del sistema

- Forma parte de la capa HTTP y expone contrato público o interno del backend.

## Observaciones

- Sin observaciones adicionales relevantes a partir del análisis estático actual.

## Relacionado

- [[python/app/api/INDEX]]
- [[RUNTIME_FLOW]]
- [[GLOSSARY]]
