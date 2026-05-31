# app/main.py

## Rol

Punto de entrada ASGI del backend principal y ensamblador de routers/dependencias.

## Identidad técnica

- Ruta real: `app/main.py`
- Tipo: `backend`
- Ámbito: `backend principal`
- Módulo lógico: `app.main`

## Símbolos principales

- Funciones: `_merge_origins`, `_resolve_cors_allowed_origins`, `_configure_cors`, `log_rejected_cors_preflight`, `_build_chat_dependencies`, `_build_chat_service`, `run_chat_request`, `_run_chat_request`, `log_runtime_configuration`

## Dependencias internas directas

- [[python/DB/chunks/document_context|DB/chunks/document_context.py]]: importa `DB.chunks.document_context.build_document_prompt`.
- [[python/app/api/__init__|app/api/__init__.py]]: importa `app.api.chat_router`, `app.api.chat_runs_router`, `app.api.evals_router`, `app.api.health_router`, `app.api.models_router`, `app.api.traces_router`.
- [[python/app/auth|app/auth.py]]: importa `app.auth.bearer_scheme`, `app.auth.require_chat_access`.
- [[python/app/chat/__init__|app/chat/__init__.py]]: importa `app.chat.ChatDependencies`, `app.chat.ChatService`.
- [[python/app/chat_eval_runner|app/chat_eval_runner.py]]: importa `app.chat_eval_runner`.
- [[python/app/chat_runs/router|app/chat_runs/router.py]]: importa `app.chat_runs.router.router`.
- [[python/app/config|app/config.py]]: importa `app.config.settings`.
- [[python/app/evals/router|app/evals/router.py]]: importa `app.evals.router.router`.
- [[python/app/llm_client|app/llm_client.py]]: importa `app.llm_client.ask_chat`, `app.llm_client.list_chat_models`, `app.llm_client.resolve_provider_model`.
- [[python/app/observability/chat_runs|app/observability/chat_runs.py]]: importa `app.observability.chat_runs.clear_chat_runs`, `app.observability.chat_runs.list_chat_runs`, `app.observability.chat_runs.save_chat_run`.
- [[python/app/observability/logging|app/observability/logging.py]]: importa `app.observability.logging.get_logger`, `app.observability.logging.log_event`.
- [[python/app/observability/trace|app/observability/trace.py]]: importa `app.observability.trace.new_trace_id`.
- [[python/app/rag_client|app/rag_client.py]]: importa `app.rag_client.query_remote_rag`.
- [[python/app/schemas|app/schemas.py]]: importa `app.schemas.ChatRequest`, `app.schemas.ChatResponse`.
- [[python/app/testclient_compat|app/testclient_compat.py]]: importa `app.testclient_compat.apply_blocking_portal_compat_patch`.
- [[python/app/tools/create_document|app/tools/create_document.py]]: importa `app.tools.create_document.create_document_tool`.

## Dependencias inversas

- [[python/tests/test_api_health|tests/test_api_health.py]]: depende de este archivo vía `app.main.app`.
- [[python/tests/test_chat_contract|tests/test_chat_contract.py]]: depende de este archivo vía `app.main.app`.
- [[python/tests/test_chat_create_document_command|tests/test_chat_create_document_command.py]]: depende de este archivo vía `app.main.app`.
- [[python/tests/test_chat_eval_foundation|tests/test_chat_eval_foundation.py]]: depende de este archivo vía `app.main.app`.
- [[python/tests/test_chat_only_runtime|tests/test_chat_only_runtime.py]]: depende de este archivo vía `app.main.app`.
- [[python/tests/test_chat_run_observability|tests/test_chat_run_observability.py]]: depende de este archivo vía `app.main.app`.
- [[python/tests/test_chat_service|tests/test_chat_service.py]]: depende de este archivo vía `app.main.app`.
- [[python/tests/test_chat_temperature_contract|tests/test_chat_temperature_contract.py]]: depende de este archivo vía `app.main.app`.
- [[python/tests/test_dev_token_auth|tests/test_dev_token_auth.py]]: depende de este archivo vía `app.main`, `app.main.app`.
- [[python/tests/test_rag_no_evidence_contract|tests/test_rag_no_evidence_contract.py]]: depende de este archivo vía `app.main.app`.
- [[python/tests/test_remote_rag_service|tests/test_remote_rag_service.py]]: depende de este archivo vía `app.main.app`.
- [[python/tests/test_runs_router|tests/test_runs_router.py]]: depende de este archivo vía `app.main.app`.

## Imports externos observados

- Paquetes o módulos externos detectados: `fastapi`

## Relación dentro del sistema

- Actúa como ensamblador principal del backend y conecta routers, runtime y dependencias compartidas.

## Observaciones

- Ensambla routers y dependencias; es una pieza clave para comprender el backend completo.

## Relacionado

- [[python/app/INDEX]]
- [[RUNTIME_FLOW]]
- [[GLOSSARY]]
