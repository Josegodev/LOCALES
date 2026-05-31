# app/llm_client.py

## Ruta real

`app/llm_client.py`

## Responsabilidad observada

Resuelve `provider/model` y delega al adaptador correcto.

## Funciones principales

- `resolve_provider_model(...)`
- `ask_chat(...)`
- `list_chat_models()`

## Quién lo llama

- `app/chat_runtime.py`
- `app/main.py`

## A quién llama

- `app/adapters/ollama_client.py`
- `app/adapters/openai_client.py`

## Entradas

- `message`
- `provider`
- `model`
- `temperature`
- `top_p`
- `max_tokens`

## Salidas

- payload de respuesta normalizado

## Efectos secundarios

- ninguno propio más allá de delegación

## Riesgos

- concentra la semántica real de `provider/model`

## Relacionado

- [[PROVIDER_BRANCH]]
- [[PROVIDER_MODEL]]
- [[OLLAMA_CLIENT_FILE]]
- [[OPENAI_CLIENT_FILE]]
