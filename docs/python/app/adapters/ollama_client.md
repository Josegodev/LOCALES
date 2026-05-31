# app/adapters/ollama_client.py

## Rol

Adaptador de proveedor LLM con contrato normalizado hacia el runtime.

## Identidad técnica

- Ruta real: `app/adapters/ollama_client.py`
- Tipo: `adapter`
- Ámbito: `backend principal`
- Módulo lógico: `app.adapters.ollama_client`

## Símbolos principales

- Clases: `OllamaClientError`
- Funciones: `_api_chat_url`, `_chat_completions_url`, `_api_tags_url`, `_selected_model`, `_timeout_seconds`, `_error_from_response`, `list_models`, `ask_chat`

## Dependencias internas directas

- [[python/app/config|app/config.py]]: importa `app.config.settings`.
- [[python/app/llm_errors|app/llm_errors.py]]: importa `app.llm_errors.LLMClientError`.

## Dependencias inversas

- [[python/app/llm_client|app/llm_client.py]]: depende de este archivo vía `app.adapters.ollama_client.ask_chat`, `app.adapters.ollama_client.list_models`.

## Imports externos observados

- Paquetes o módulos externos detectados: `requests`

## Relación dentro del sistema

- Su relación operativa exacta requiere contexto adicional del flujo donde se invoca.

## Observaciones

- Sin observaciones adicionales relevantes a partir del análisis estático actual.

## Relacionado

- [[python/app/adapters/INDEX]]
- [[ARCHITECTURE]]
- [[GLOSSARY]]
