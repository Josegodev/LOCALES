# RAG_BRANCH

## Cuándo se activa

RAG se activa cuando:

- `use_rag=true`
- el mensaje no entra por `/creardoc`

Si `use_rag=false` o el flujo es `/creardoc`:

- `retrieval_status="DISABLED"`

## RAG local

- módulo: `DB/chunks/document_context.py`
- llamada desde runtime: `build_document_prompt(...)`
- fuente principal: `DB/chunks/documents.sqlite`

## RAG remoto

- cliente: `app/rag_client.py`
- servicio: `rag_service/main.py`
- endpoint: `POST /rag/query`

El cliente remoto transporta:

- `query`
- `top_k`
- `trace_id`
- `allowed_source_filenames`
- `active_document_id` si aplica
- `active_document_title` si aplica
- `active_corpus` si aplica
- `last_source_intent` si aplica

## Evidencia que viaja

- `chunks`
- `chunk_ids`
- `document_ids`
- `source_filenames`
- `candidate_filenames`
- `selected_filenames`
- `scores`
- `ranking_scores`

## `retrieval_status`

Valores observados:

- `EVIDENCE_FOUND`
- `NO_EVIDENCE`
- `NO_EVIDENCE_FOR_ANSWER`
- `DISABLED`
- `unknown`
- `RAG_ERROR` pendiente de confirmar como valor público estable

## Evidencia encontrada vs no encontrada

### Evidencia encontrada

- `retrieval_status="EVIDENCE_FOUND"`
- puede haber `chunk_ids` y `source_filenames`
- suele terminar en `documentary_answer`

### No evidencia

- `retrieval_status` cae en `NO_EVIDENCE` o `NO_EVIDENCE_FOR_ANSWER`
- `fallback_used=true`
- se limpia evidencia pública si no es fiable
- no se permite respuesta libre documental

## Riesgos principales

- evidencia insuficiente con apariencia inicial de éxito;
- diferencias sutiles entre RAG local y remoto;
- `warnings` heterogéneos;
- drift entre servicio remoto y cliente;
- corpus ambiguo si no hay filtros claros.

## Relaciones verificadas

- `call`: `app/chat_runtime.py -> DB/chunks/document_context.py`
- `call`: `app/chat_runtime.py -> app/rag_client.py`
- `call`: `app/rag_client.py -> POST /rag/query`
- `call`: `rag_service/main.py -> DB/chunks/document_context.py`
- `test`: `tests/test_remote_rag_service.py`, `tests/test_rag_no_evidence_contract.py`

## Relacionado

- [[POST_CHAT_FLOW]]
- [[RAG_EVIDENCE]]
- [[DOCUMENT_CONTEXT_FILE]]
- [[RAG_CLIENT_FILE]]
- [[RAG_SERVICE_MAIN_FILE]]
