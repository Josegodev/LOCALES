# app/schemas.py

## Rol

Archivo Python con clases y funciones de soporte del sistema.

## Identidad técnica

- Ruta real: `app/schemas.py`
- Tipo: `backend`
- Ámbito: `backend principal`
- Módulo lógico: `app.schemas`

## Símbolos principales

- Clases: `CreateDocumentRequest`, `ChatRequest`, `ChatResponse`, `ChatModelOption`, `ChatModelListResponse`, `ChatTemperaturePreset`, `ChatTemperatureOptions`, `ChatOptionsResponse`, `ErrorResponse`, `ChatRunResponse`, `ChatTraceResponse`, `ChatRunListResponse`, `ChatTraceListResponse`, `ChatTraceResetResponse`, `ChatEvalListResponse`, `ChatSavedRunResponse`, `ChatRunsStatsResponse`, `ChatEvalFailure`, `ChatEvalResultResponse`, `ChatEvalRunSummary`, `ChatEvalSavedRunItem`, `ChatEvalRunsListResponse`, `ChatEvalRunResponse`
- Funciones: `normalize_temperature`, `normalize_top_p`

## Dependencias internas directas

- No se han detectado imports internos directos del repositorio.

## Dependencias inversas

- [[python/app/api/routes_chat|app/api/routes_chat.py]]: depende de este archivo vía `app.schemas.ChatRequest`, `app.schemas.ChatResponse`.
- [[python/app/api/routes_chat_runs|app/api/routes_chat_runs.py]]: depende de este archivo vía `app.schemas.ChatRunListResponse`.
- [[python/app/api/routes_evals|app/api/routes_evals.py]]: depende de este archivo vía `app.schemas.ChatEvalListResponse`, `app.schemas.ChatEvalRunResponse`, `app.schemas.ChatEvalRunsListResponse`, `app.schemas.ChatRequest`.
- [[python/app/api/routes_models|app/api/routes_models.py]]: depende de este archivo vía `app.schemas.ChatModelListResponse`, `app.schemas.ChatOptionsResponse`, `app.schemas.TEMPERATURE_DEFAULT`, `app.schemas.TEMPERATURE_MAX`, `app.schemas.TEMPERATURE_MIN`.
- [[python/app/api/routes_traces|app/api/routes_traces.py]]: depende de este archivo vía `app.schemas.ChatTraceListResponse`, `app.schemas.ChatTraceResetResponse`.
- [[python/app/chat/response_builder|app/chat/response_builder.py]]: depende de este archivo vía `app.schemas.ChatResponse`.
- [[python/app/chat/retrieval|app/chat/retrieval.py]]: depende de este archivo vía `app.schemas.ChatRequest`.
- [[python/app/chat/service|app/chat/service.py]]: depende de este archivo vía `app.schemas.ChatRequest`, `app.schemas.ChatResponse`.
- [[python/app/chat_runs/store|app/chat_runs/store.py]]: depende de este archivo vía `app.schemas.normalize_temperature`.
- [[python/app/chat_runtime|app/chat_runtime.py]]: depende de este archivo vía `app.schemas.ChatRequest`, `app.schemas.ChatResponse`, `app.schemas.TEMPERATURE_DEFAULT`.
- [[python/app/evals/loader|app/evals/loader.py]]: depende de este archivo vía `app.schemas.normalize_temperature`.
- [[python/app/main|app/main.py]]: depende de este archivo vía `app.schemas.ChatRequest`, `app.schemas.ChatResponse`.
- [[python/app/observability/chat_runs|app/observability/chat_runs.py]]: depende de este archivo vía `app.schemas.normalize_temperature`, `app.schemas.normalize_top_p`.
- [[python/app/tools/create_document|app/tools/create_document.py]]: depende de este archivo vía `app.schemas.CreateDocumentRequest`.
- [[python/tests/test_chat_contract|tests/test_chat_contract.py]]: depende de este archivo vía `app.schemas.ChatResponse`.
- [[python/tests/test_chat_retrieval|tests/test_chat_retrieval.py]]: depende de este archivo vía `app.schemas.ChatRequest`.
- [[python/tests/test_chat_service|tests/test_chat_service.py]]: depende de este archivo vía `app.schemas.ChatRequest`, `app.schemas.ChatResponse`.
- [[python/tests/test_create_document_tool|tests/test_create_document_tool.py]]: depende de este archivo vía `app.schemas.CreateDocumentRequest`.
- [[python/tests/test_schemas_contract|tests/test_schemas_contract.py]]: depende de este archivo vía `app.schemas.ChatRequest`, `app.schemas.ChatResponse`.

## Imports externos observados

- Paquetes o módulos externos detectados: `math`, `pathlib`, `pydantic`, `typing`, `uuid`

## Relación dentro del sistema

- Su relación operativa exacta requiere contexto adicional del flujo donde se invoca.

## Observaciones

- Sin observaciones adicionales relevantes a partir del análisis estático actual.

## Relacionado

- [[python/app/INDEX]]
- [[ARCHITECTURE]]
- [[GLOSSARY]]
