# DB/chunks/run_ingest_pipeline.py

## Rol

Script o módulo del pipeline documental local de RAG.

## Identidad técnica

- Ruta real: `DB/chunks/run_ingest_pipeline.py`
- Tipo: `rag_local`
- Ámbito: `RAG local y base documental`
- Módulo lógico: `DB.chunks.run_ingest_pipeline`

## Símbolos principales

- Funciones: `default_pdf_path`, `run_ingest`, `validate_sqlite`, `validate_search`, `validate_document_context`, `main`

## Dependencias internas directas

- [[python/DB/chunks/document_context|DB/chunks/document_context.py]]: importa `document_context.build_document_prompt`.
- [[python/DB/chunks/search_docs|DB/chunks/search_docs.py]]: importa `search_docs.search_chunks`.

## Dependencias inversas

- No se han detectado dependencias internas inversas dentro del inventario analizado.

## Imports externos observados

- Paquetes o módulos externos detectados: `argparse`, `pathlib`, `sqlite3`, `subprocess`, `sys`

## Relación dentro del sistema

- Está conectado con la cadena de recuperación documental y construcción de contexto RAG.

## Observaciones

- Sin observaciones adicionales relevantes a partir del análisis estático actual.

## Relacionado

- [[python/DB/chunks/INDEX]]
- [[RAG_AND_EVIDENCE]]
- [[GLOSSARY]]
