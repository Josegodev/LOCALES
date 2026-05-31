# app/config.py

## Rol

Archivo Python centrado en clases o tipos de soporte.

## Identidad técnica

- Ruta real: `app/config.py`
- Tipo: `backend`
- Ámbito: `backend principal`
- Módulo lógico: `app.config`

## Símbolos principales

- Clases: `Settings`

## Dependencias internas directas

- No se han detectado imports internos directos del repositorio.

## Dependencias inversas

- [[python/DB/chunks/document_context|DB/chunks/document_context.py]]: depende de este archivo vía `app.config.settings`.
- [[python/app/adapters/ollama_client|app/adapters/ollama_client.py]]: depende de este archivo vía `app.config.settings`.
- [[python/app/adapters/openai_client|app/adapters/openai_client.py]]: depende de este archivo vía `app.config.settings`.
- [[python/app/auth|app/auth.py]]: depende de este archivo vía `app.config.settings`.
- [[python/app/chat/dependencies|app/chat/dependencies.py]]: depende de este archivo vía `app.config.Settings`.
- [[python/app/chat_runtime|app/chat_runtime.py]]: depende de este archivo vía `app.config.settings`.
- [[python/app/evals/router|app/evals/router.py]]: depende de este archivo vía `app.config.settings`.
- [[python/app/llm_client|app/llm_client.py]]: depende de este archivo vía `app.config.settings`.
- [[python/app/main|app/main.py]]: depende de este archivo vía `app.config.settings`.
- [[python/app/observability/chat_runs|app/observability/chat_runs.py]]: depende de este archivo vía `app.config.settings`.
- [[python/app/observability/chat_trace|app/observability/chat_trace.py]]: depende de este archivo vía `app.config.settings`.
- [[python/app/rag_client|app/rag_client.py]]: depende de este archivo vía `app.config.settings`.
- [[python/rag_service/main|rag_service/main.py]]: depende de este archivo vía `app.config.settings`.
- [[python/scripts/audit_documents_db|scripts/audit_documents_db.py]]: depende de este archivo vía `app.config.settings`.
- [[python/scripts/probe_openai_models|scripts/probe_openai_models.py]]: depende de este archivo vía `app.config.settings`.
- [[python/tests/test_chat_service|tests/test_chat_service.py]]: depende de este archivo vía `app.config.settings`.
- [[python/tests/test_remote_rag_service|tests/test_remote_rag_service.py]]: depende de este archivo vía `app.config.settings`.

## Imports externos observados

- Paquetes o módulos externos detectados: `pathlib`, `pydantic`, `pydantic_settings`, `typing`

## Relación dentro del sistema

- Su relación operativa exacta requiere contexto adicional del flujo donde se invoca.

## Observaciones

- Sin observaciones adicionales relevantes a partir del análisis estático actual.

## Relacionado

- [[python/app/INDEX]]
- [[ARCHITECTURE]]
- [[GLOSSARY]]
