# RAG

## Responsabilidad

Recupera contexto documental antes de generar una respuesta.

## Entradas

- `message`
- `top_k`
- filtros por fichero
- contexto activo de documento

## Salidas

- `prompt`
- `retrieval_status`
- `chunks`
- `chunk_ids`
- `document_ids`
- `source_filenames`

## Módulos relacionados

- `DB/chunks/document_context.py`
- `app/rag_client.py`
- `rag_service/main.py`

## Fallos posibles

- no evidencia
- error remoto
- drift local/remoto
- warnings heterogéneos

## Relacionado

- [[RAG_BRANCH]]
- [[RAG_EVIDENCE]]
- [[DOCUMENT_CONTEXT_FILE]]
- [[RAG_CLIENT_FILE]]
