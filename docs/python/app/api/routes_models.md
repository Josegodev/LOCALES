# app/api/routes_models.py

## Rol

Router FastAPI especializado en una superficie concreta de la API.

## Identidad técnica

- Ruta real: `app/api/routes_models.py`
- Tipo: `router`
- Ámbito: `backend principal`
- Módulo lógico: `app.api.routes_models`

## Símbolos principales

- Funciones: `chat_models`, `chat_options`

## Dependencias internas directas

- [[python/app/api/runtime_bridge|app/api/runtime_bridge.py]]: importa `app.api.runtime_bridge.main_module`.
- [[python/app/schemas|app/schemas.py]]: importa `app.schemas.ChatModelListResponse`, `app.schemas.ChatOptionsResponse`, `app.schemas.TEMPERATURE_DEFAULT`, `app.schemas.TEMPERATURE_MAX`, `app.schemas.TEMPERATURE_MIN`.

## Dependencias inversas

- [[python/app/api/__init__|app/api/__init__.py]]: depende de este archivo vía `app.api.routes_models.router`.

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
