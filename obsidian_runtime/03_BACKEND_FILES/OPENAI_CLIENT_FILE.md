# app/adapters/openai_client.py

## Ruta real

`app/adapters/openai_client.py`

## Responsabilidad observada

Llama a OpenAI y devuelve respuesta normalizada con menos métricas nativas.

## Funciones principales

- `resolve_model(...)`
- `ask_chat(...)`

## Quién lo llama

- `app/llm_client.py`

## A quién llama

- SDK OpenAI

## Entradas

- `message`
- `model`
- `temperature`
- `top_p`
- `max_tokens`

## Salidas

- `answer`
- `provider`
- `model`
- `latency_ms`
- `temperature_ignored`

## Riesgos

- depende de API key y red
- métrica menos rica que Ollama

## Relacionado

- [[LLM_PROVIDER]]
- [[PROVIDER_BRANCH]]
- [[TELEMETRY]]
