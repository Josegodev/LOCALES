# CHAT_REQUEST

## Contrato observado

`ChatRequest` vive en `app/schemas.py`.

## Campos

- `message`: obligatorio, `1..4000`
- `provider`: opcional
- `model`: opcional en schema, obligatorio en runtime
- `max_tokens`: `1..2048`
- `temperature`: `0.0..1.5`
- `top_p`: `0.0..1.0`
- `use_rag`: default `True`
- `top_k`: default `3`, rango `1..10`
- `trace_id`: UUID con o sin guiones
- `user_id`, `chat_id`
- `allowed_source_filenames`
- `active_document_id`
- `active_document_title`
- `active_corpus`
- `last_source_intent`

## Validaciones

- schema FastAPI/Pydantic
- saneado de `allowed_source_filenames` a basename
- `model` exigido después en runtime

## Riesgo de drift

- `model` opcional en schema pero obligatorio en ejecución

## Relacionado

- [[POST_CHAT_FLOW]]
- [[CHAT_RESPONSE]]
- [[ERRORS]]
