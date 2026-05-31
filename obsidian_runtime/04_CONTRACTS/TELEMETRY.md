# TELEMETRY

## Señales mínimas fiables

- `trace_id`
- `status`
- `provider`
- `model`
- `retrieval_status`
- `fallback_used`
- `latency_ms`
- `chunk_ids`
- `source_filenames`

## Métricas públicas

- `prompt_eval_count`
- `eval_count`
- `prompt_eval_duration`
- `eval_duration`
- `total_duration`
- `load_duration`

## Métricas persistidas pero no públicas

- `tokens_input`
- `tokens_output`
- `tokens_total`
- `generation_latency_ms`
- `retrieval_latency_ms`
- `error_type`

## Fiabilidad por proveedor

- Ollama: más rica
- OpenAI: más pobre en métricas nativas

## Riesgo de drift

- la respuesta pública no refleja toda la observabilidad persistida

## Relacionado

- [[OBSERVABILITY]]
- [[CHAT_RESPONSE]]
- [[CHAT_RUNS_FILE]]
