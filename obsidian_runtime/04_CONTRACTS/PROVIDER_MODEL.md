# PROVIDER_MODEL

## Contrato observado

La validación real se hace en `app/llm_client.py`.

## Reglas

- default `provider=ollama`
- `provider=ollama` no acepta `gpt-*`
- `provider=openai` no acepta modelos no OpenAI
- `provider` desconocido falla

## Qué pasa si falta `model`

- el runtime devuelve `400 model_required`
- esto ocurre antes de explotar algunos defaults del cliente LLM

## Riesgo de drift

- el schema no expresa toda la semántica del contrato

## Relacionado

- [[PROVIDER_BRANCH]]
- [[ERRORS]]
- [[LLM_CLIENT_FILE]]
