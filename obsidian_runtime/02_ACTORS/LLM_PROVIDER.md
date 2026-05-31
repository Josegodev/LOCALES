# LLM_PROVIDER

## Responsabilidad

Genera la respuesta final cuando el runtime decide llamar al modelo.

## Entradas

- `message`
- `provider`
- `model`
- `temperature`
- `top_p`
- `max_tokens`
- `system_prompt` en algunos flujos

## Salidas

- `answer`
- `provider`
- `model`
- métricas del proveedor cuando existen

## Módulos relacionados

- `app/llm_client.py`
- `app/adapters/ollama_client.py`
- `app/adapters/openai_client.py`

## Fallos posibles

- timeout
- auth error
- model not available
- rate limit
- proveedor no disponible

## Relacionado

- [[PROVIDER_BRANCH]]
- [[PROVIDER_MODEL]]
- [[OLLAMA_CLIENT_FILE]]
- [[OPENAI_CLIENT_FILE]]
