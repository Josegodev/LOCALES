# DB/chunks/search_docs.py

## Rol

Script o módulo del pipeline documental local de RAG.

## Identidad técnica

- Ruta real: `DB/chunks/search_docs.py`
- Tipo: `rag_local`
- Ámbito: `RAG local y base documental`
- Módulo lógico: `DB.chunks.search_docs`

## Símbolos principales

- Funciones: `search_chunks`, `main`

## Dependencias internas directas

- [[python/DB/chunks/document_context|DB/chunks/document_context.py]]: importa `document_context.search_chunks`.

## Dependencias inversas

- [[python/DB/chunks/run_ingest_pipeline|DB/chunks/run_ingest_pipeline.py]]: depende de este archivo vía `search_docs.search_chunks`.
- [[python/tests/test_retrieval_path_consistency|tests/test_retrieval_path_consistency.py]]: depende de este archivo vía `DB.chunks.search_docs`.

## Imports externos observados

- Paquetes o módulos externos detectados: `DB`, `argparse`

## Relación dentro del sistema

- Está conectado con la cadena de recuperación documental y construcción de contexto RAG.

## Observaciones

- Sin observaciones adicionales relevantes a partir del análisis estático actual.

## Relacionado

- [[python/DB/chunks/INDEX]]
- [[RAG_AND_EVIDENCE]]
- [[GLOSSARY]]
