# Flujo: ingesta documental y RAG

```text
PDF/Markdown
  -> DB/chunks/ingest_pdf_markdown.py o ingest_nucleo_md.py
  -> DB/chunks/documents.sqlite
  -> DB/chunks/search_docs.py / document_context.py
  -> prompt con EVIDENCIA
  -> LM Studio
```

## Contratos

- Tabla `documents`: `filename`, `source_path`, `sha256`, `raw_markdown`, `created_at`.
- Tabla `chunks`: `document_id`, `chunk_index`, `text`, `char_count`, `created_at`.
- Busqueda: scoring por presencia de terminos, no embeddings.

## Riesgos

- No hay ranking semantico; coincidencias simples pueden recuperar evidencia irrelevante.
- `ingest_pdf_markdown.py` usa `DB_PATH="documents.sqlite"` relativo al cwd; scripts wrapper fuerzan cwd, ejecucion manual puede escribir en otro sitio.
