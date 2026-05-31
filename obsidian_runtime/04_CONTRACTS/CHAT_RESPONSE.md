# CHAT_RESPONSE

## Contrato observado

`ChatResponse` vive en `app/schemas.py` y modela la respuesta exitosa pública.

## Campos principales

- `trace_id`
- `status`
- `provider`
- `model`
- `temperature`
- `temperature_ignored`
- `use_rag`
- `answer`
- `latency_ms`
- `retrieval_status`
- `answer_mode`
- `evidence_used`
- `fallback_used`
- `chunk_ids`
- `document_ids`
- `source_filenames`
- `warnings`

## Campos métricos públicos

- `prompt_eval_count`
- `eval_count`
- `prompt_eval_duration`
- `eval_duration`
- `total_duration`
- `load_duration`

## Campos de tool

- `command`
- `tool_called`
- `tool_result_status`
- `document_path`
- `document_filename`

## Riesgo de drift

- hay métricas persistidas que no salen en `ChatResponse`
- el contrato de error no usa este schema

## Relacionado

- [[CHAT_REQUEST]]
- [[TELEMETRY]]
- [[ERRORS]]
