# PROVIDER_BRANCH

## Selección de proveedor

La selección real se hace en `app/llm_client.py::resolve_provider_model(...)`.

Regla observada:

- si `provider` falta, usa `ollama`
- `provider` se normaliza con `strip().lower()`

## Selección de modelo

### Ollama

- usa el modelo recibido si es válido
- si falta, intenta el configurado
- si sigue faltando, intenta el primer modelo disponible
- acepta resolución por prefijo único

### OpenAI

- si falta, usa `DEFAULT_OPENAI_MODEL`
- valida contra `SUPPORTED_MODELS`

## Validaciones

- `provider=ollama` no acepta `gpt-*`
- `provider=openai` no acepta modelos no OpenAI
- `provider` desconocido falla

## Adaptadores

- `app/adapters/ollama_client.py`
- `app/adapters/openai_client.py`

## Diferencias de métricas

### Ollama

Puede devolver:

- `prompt_eval_count`
- `eval_count`
- `prompt_eval_duration`
- `eval_duration`
- `total_duration`
- `load_duration`

### OpenAI

Devuelve de forma observada:

- `latency_ms`
- `temperature_ignored`
- `answer`

No devuelve en el adaptador inspeccionado el mismo nivel métrico que Ollama.

## Errores posibles

- `invalid_provider_model_pair`
- `llm_unavailable`
- `llm_network_error`
- `llm_timeout`
- `llm_model_not_available`
- `llm_auth_error`
- `llm_rate_limited`

## Coste operacional y lock-in

- Ollama depende de disponibilidad local y del inventario de modelos locales.
- OpenAI depende de API key, red y coste monetario externo.
- La asimetría métrica hace comparaciones cruzadas más difíciles.

## Relaciones verificadas

- `call`: `app/chat_runtime.py -> app/llm_client.py`
- `call`: `app/llm_client.py -> app/adapters/ollama_client.py`
- `call`: `app/llm_client.py -> app/adapters/openai_client.py`
- `test`: `tests/test_provider_model_resolution.py`, `tests/test_chat_only_runtime.py`

## Relacionado

- [[POST_CHAT_FLOW]]
- [[PROVIDER_MODEL]]
- [[LLM_CLIENT_FILE]]
- [[OLLAMA_CLIENT_FILE]]
- [[OPENAI_CLIENT_FILE]]
