# app/llm_errors.py

## Rol

Archivo Python centrado en clases o tipos de soporte.

## Identidad técnica

- Ruta real: `app/llm_errors.py`
- Tipo: `backend`
- Ámbito: `backend principal`
- Módulo lógico: `app.llm_errors`

## Símbolos principales

- Clases: `LLMClientError`

## Dependencias internas directas

- No se han detectado imports internos directos del repositorio.

## Dependencias inversas

- [[python/app/adapters/ollama_client|app/adapters/ollama_client.py]]: depende de este archivo vía `app.llm_errors.LLMClientError`.
- [[python/app/adapters/openai_client|app/adapters/openai_client.py]]: depende de este archivo vía `app.llm_errors.LLMClientError`.
- [[python/app/chat/fallback|app/chat/fallback.py]]: depende de este archivo vía `app.llm_errors.LLMClientError`.
- [[python/app/llm_client|app/llm_client.py]]: depende de este archivo vía `app.llm_errors.LLMClientError`.

## Imports externos observados

- No se han detectado imports externos explícitos.

## Relación dentro del sistema

- Su relación operativa exacta requiere contexto adicional del flujo donde se invoca.

## Observaciones

- Sin observaciones adicionales relevantes a partir del análisis estático actual.

## Relacionado

- [[python/app/INDEX]]
- [[ARCHITECTURE]]
- [[GLOSSARY]]
