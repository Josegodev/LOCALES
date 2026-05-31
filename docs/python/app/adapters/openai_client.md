# app/adapters/openai_client.py

## Rol

Adaptador de proveedor LLM con contrato normalizado hacia el runtime.

## Identidad técnica

- Ruta real: `app/adapters/openai_client.py`
- Tipo: `adapter`
- Ámbito: `backend principal`
- Módulo lógico: `app.adapters.openai_client`

## Símbolos principales

- Clases: `OpenAIClientError`
- Funciones: `resolve_model`, `_build_client`, `_error_from_exception`, `_temperature_rejected`, `_response_text`, `ask_chat`

## Dependencias internas directas

- [[python/app/config|app/config.py]]: importa `app.config.settings`.
- [[python/app/llm_errors|app/llm_errors.py]]: importa `app.llm_errors.LLMClientError`.

## Dependencias inversas

- [[python/app/llm_client|app/llm_client.py]]: depende de este archivo vía `app.adapters.openai_client.DEFAULT_OPENAI_MODEL`, `app.adapters.openai_client.SUPPORTED_MODELS`, `app.adapters.openai_client.ask_chat`, `app.adapters.openai_client.resolve_model`.

## Imports externos observados

- Paquetes o módulos externos detectados: `openai`, `time`, `typing`

## Relación dentro del sistema

- Su relación operativa exacta requiere contexto adicional del flujo donde se invoca.

## Observaciones

- Sin observaciones adicionales relevantes a partir del análisis estático actual.

## Relacionado

- [[python/app/adapters/INDEX]]
- [[ARCHITECTURE]]
- [[GLOSSARY]]
