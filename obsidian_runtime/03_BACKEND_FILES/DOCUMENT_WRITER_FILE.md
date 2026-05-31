# app/services/document_writer.py

## Ruta real

`app/services/document_writer.py`

## Responsabilidad observada

Escribe el documento final en disco para la rama `/creardoc`.

## Funciones principales

- `slugify(...)`
- `write_document(...)`

## Quién lo llama

- `app/tools/create_document.py`

## Entradas

- `content`
- `trace_id`
- `filename`

## Salidas

- resultado de escritura con `status` y metadatos

## Efectos secundarios

- escritura en `outputs/documents/`

## Riesgos

- participa solo en la rama de tool, no en el chat normal

## Relacionado

- [[CREATE_DOCUMENT_TOOL_FILE]]
- [[POST_CHAT_FLOW]]
- [[ERROR_AND_FALLBACK_FLOW]]
