# app/tools/create_document.py

## Ruta real

`app/tools/create_document.py`

## Responsabilidad observada

Implementa la rama `/creardoc` del runtime.

## Funciones principales

- `build_create_document_request(...)`
- `create_document_tool(...)`

## Quién lo llama

- `app/chat_runtime.py`

## A quién llama

- `app/services/document_writer.write_document(...)`

## Entradas

- request documental
- contenido generado por el LLM

## Salidas

- estado de tool
- `document_path`
- `document_filename`
- `chars_written`

## Riesgos

- es una rama especial dentro del mismo contrato `/chat`

## Relacionado

- [[POST_CHAT_FLOW]]
- [[ERROR_AND_FALLBACK_FLOW]]
- [[CHAT_RESPONSE]]
