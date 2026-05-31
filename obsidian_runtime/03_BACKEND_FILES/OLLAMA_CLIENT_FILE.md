# app/adapters/ollama_client.py

## Ruta real

`app/adapters/ollama_client.py`

## Responsabilidad observada

Llama a Ollama y devuelve respuesta con métricas nativas ricas.

## Funciones principales

- `list_models(...)`
- `ask_chat(...)`

## Quién lo llama

- `app/llm_client.py`

## A quién llama

- API HTTP de Ollama

## Entradas

- `message`
- `model`
- `temperature`
- `top_p`
- `num_predict`

## Salidas

- `answer`
- `provider`
- `model`
- `prompt_eval_count`
- `eval_count`
- `prompt_eval_duration`
- `eval_duration`
- `total_duration`
- `load_duration`

## Riesgos

- dependencia operativa local
- timeout o falta de modelos disponibles

## Relacionado

- [[LLM_PROVIDER]]
- [[PROVIDER_BRANCH]]
- [[TELEMETRY]]
