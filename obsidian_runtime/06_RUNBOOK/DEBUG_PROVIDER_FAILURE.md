# DEBUG_PROVIDER_FAILURE

## Objetivo

Diagnosticar fallos en la llamada al modelo.

## Checklist

1. revisar `provider` y `model`
2. confirmar si la pareja es válida
3. revisar disponibilidad de Ollama o API key OpenAI
4. distinguir timeout, auth, model missing o rate limit
5. revisar si `temperature_ignored=true`

## Relacionado

- [[PROVIDER_BRANCH]]
- [[PROVIDER_MODEL]]
- [[ERRORS]]
