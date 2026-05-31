# ERRORS

## Errores de schema y acceso

- `422` payload incompatible con `ChatRequest`
- `403` acceso rechazado

## Errores de contrato runtime

- `400 model_required`
- `400 invalid_provider_model_pair`

## Errores de proveedor

- `401 llm_auth_error`
- `404 llm_model_not_available`
- `429 llm_rate_limited`
- `503 llm_unavailable` o `llm_network_error`
- `504 llm_timeout`

## Errores RAG

- degradación a `NO_EVIDENCE_FOR_ANSWER`
- safe refusal sin generación libre

## Errores de persistencia

- el chat puede responder y aun así fallar `save_chat_run`

## Riesgo de drift

- los errores se devuelven como `HTTPException.detail`, no como un modelo de error único

## Relacionado

- [[ERROR_AND_FALLBACK_FLOW]]
- [[CHAT_REQUEST]]
- [[CHAT_RESPONSE]]
