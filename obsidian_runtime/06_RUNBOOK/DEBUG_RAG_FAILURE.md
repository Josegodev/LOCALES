# DEBUG_RAG_FAILURE

## Objetivo

Diagnosticar por qué el flujo RAG no devuelve evidencia útil.

## Checklist

1. confirmar `use_rag=true`
2. confirmar rama local o remota
3. revisar `retrieval_status`
4. revisar `chunk_ids` y `source_filenames`
5. revisar filtros `allowed_source_filenames`
6. confirmar si hubo degradación a `NO_EVIDENCE_FOR_ANSWER`

## Riesgos típicos

- servicio remoto caído
- corpus ambiguo
- evidencia inicial pero respuesta marker-only
- warnings perdidos o heterogéneos

## Relacionado

- [[RAG_BRANCH]]
- [[RAG_EVIDENCE]]
- [[ERROR_AND_FALLBACK_FLOW]]
