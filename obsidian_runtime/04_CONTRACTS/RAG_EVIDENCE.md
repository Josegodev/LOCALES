# RAG_EVIDENCE

## Contrato observado

La rama RAG transporta evidencia documental hacia la respuesta pública y hacia la persistencia.

## Campos críticos

- `retrieval_status`
- `chunks`
- `chunk_ids`
- `document_ids`
- `source_filenames`
- `candidate_filenames`
- `selected_filenames`
- `scores`
- `ranking_scores`

## Estados observados

- `EVIDENCE_FOUND`
- `NO_EVIDENCE`
- `NO_EVIDENCE_FOR_ANSWER`
- `DISABLED`

`RAG_ERROR` queda `pendiente de confirmar` como contrato público estable.

## Riesgos

- evidencia insuficiente con apariencia inicial de éxito
- divergencia local/remoto
- limpieza de evidencia en safe refusal

## Relacionado

- [[RAG_BRANCH]]
- [[CHAT_RESPONSE]]
- [[DOCUMENT_CONTEXT_FILE]]
