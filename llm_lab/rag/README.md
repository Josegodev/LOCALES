# Local RAG Notes

This folder is the only document source used by `/rag/query`.

Rules for the lab:

- The query is local and deterministic.
- The search reads only files inside `llm_lab/rag`.
- A model can use retrieved context to generate text, but it cannot execute actions.
- All model output must be validated before the API returns it.
- If validation fails, the proposal fallback uses `suggested_action: "none"`.
- Every request writes a trace with input, prompt, model_id, raw_output, validated_output, fallback_used, fallback_reason, and latency_ms.

