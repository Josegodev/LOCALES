# Glosario runtime

- `trace_id`: identificador de correlación del chat.
- `retrieval_status`: estado público del retrieval.
- `safe_refusal`: respuesta segura cuando falta evidencia suficiente.
- `evidence_used`: indica si la respuesta usa evidencia documental.
- `fallback_used`: indica degradación controlada del runtime.
- `provider/model`: pareja semántica que decide qué adaptador LLM se usa.
- `RAG local`: retrieval directo sobre `DB/chunks/document_context.py`.
- `RAG remoto`: retrieval por `app/rag_client.py` y `rag_service/main.py`.
- `ChatDependencies`: paquete de dependencias inyectables del runtime.
- `run`: artefacto persistido del chat en `CHAT_RUNS/`.

## Relacionado

- [[00_START_HERE]]
- [[TELEMETRY]]
- [[CHAT_REQUEST]]
- [[CHAT_RESPONSE]]
