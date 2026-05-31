# DB/chunks/ingest_pdf_markdown.py

## Rol

Script o módulo del pipeline documental local de RAG.

## Identidad técnica

- Ruta real: `DB/chunks/ingest_pdf_markdown.py`
- Tipo: `rag_local`
- Ámbito: `RAG local y base documental`
- Módulo lógico: `DB.chunks.ingest_pdf_markdown`

## Símbolos principales

- Funciones: `now_iso`, `sha256_file`, `init_db`, `chunk_markdown`, `ingest_pdf`, `resolve_input_path`, `collect_pdf_paths`, `main`

## Dependencias internas directas

- [[python/DB/chunks/document_context|DB/chunks/document_context.py]]: importa `document_context.classify_document_metadata`, `document_context.ensure_documents_metadata_schema`.

## Dependencias inversas

- No se han detectado dependencias internas inversas dentro del inventario analizado.

## Imports externos observados

- Paquetes o módulos externos detectados: `DB`, `argparse`, `datetime`, `hashlib`, `pathlib`, `pymupdf4llm`, `sqlite3`, `sys`

## Relación dentro del sistema

- Está conectado con la cadena de recuperación documental y construcción de contexto RAG.

## Observaciones

- Sin observaciones adicionales relevantes a partir del análisis estático actual.

## Relacionado

- [[python/DB/chunks/INDEX]]
- [[RAG_AND_EVIDENCE]]
- [[GLOSSARY]]
