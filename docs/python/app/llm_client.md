# app/llm_client.py

## Rol

Archivo Python centrado en funciones utilitarias u operativas.

## Identidad técnica

- Ruta real: `app/llm_client.py`
- Tipo: `backend`
- Ámbito: `backend principal`
- Módulo lógico: `app.llm_client`

## Símbolos principales

- Funciones: `_normalize_model_name`, `_is_openai_model`, `_resolve_ollama_model`, `list_chat_models`, `resolve_provider_model`, `ask_chat`

## Dependencias internas directas

- [[python/app/adapters/ollama_client|app/adapters/ollama_client.py]]: importa `app.adapters.ollama_client.ask_chat`, `app.adapters.ollama_client.list_models`.
- [[python/app/adapters/openai_client|app/adapters/openai_client.py]]: importa `app.adapters.openai_client.DEFAULT_OPENAI_MODEL`, `app.adapters.openai_client.SUPPORTED_MODELS`, `app.adapters.openai_client.ask_chat`, `app.adapters.openai_client.resolve_model`.
- [[python/app/config|app/config.py]]: importa `app.config.settings`.
- [[python/app/llm_errors|app/llm_errors.py]]: importa `app.llm_errors.LLMClientError`.

## Dependencias inversas

- [[python/app/chat_runtime|app/chat_runtime.py]]: depende de este archivo vía `app.llm_client.LLMClientError`, `app.llm_client.ask_chat`, `app.llm_client.resolve_provider_model`.
- [[python/app/main|app/main.py]]: depende de este archivo vía `app.llm_client.ask_chat`, `app.llm_client.list_chat_models`, `app.llm_client.resolve_provider_model`.
- [[python/tests/test_chat_only_runtime|tests/test_chat_only_runtime.py]]: depende de este archivo vía `app.llm_client`.
- [[python/tests/test_provider_model_resolution|tests/test_provider_model_resolution.py]]: depende de este archivo vía `app.llm_client.LLMClientError`, `app.llm_client.resolve_provider_model`.

## Imports externos observados

- Paquetes o módulos externos detectados: `requests`

## Relación dentro del sistema

- Su relación operativa exacta requiere contexto adicional del flujo donde se invoca.

## Observaciones

- Sin observaciones adicionales relevantes a partir del análisis estático actual.

## Relacionado

- [[python/app/INDEX]]
- [[RUNTIME_FLOW]]
- [[GLOSSARY]]
