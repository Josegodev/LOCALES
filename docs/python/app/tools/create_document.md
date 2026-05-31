# app/tools/create_document.py

## Rol

Tool reutilizable invocable desde el runtime.

## Identidad técnica

- Ruta real: `app/tools/create_document.py`
- Tipo: `tool`
- Ámbito: `backend principal`
- Módulo lógico: `app.tools.create_document`

## Símbolos principales

- Funciones: `_error_result`, `_overwrite_metadata`, `build_create_document_request`, `_generate_markdown_content`, `_coerce_request`, `create_document_tool`

## Dependencias internas directas

- [[python/app/schemas|app/schemas.py]]: importa `app.schemas.CreateDocumentRequest`.
- [[python/app/services/document_writer|app/services/document_writer.py]]: importa `app.services.document_writer.slugify`, `app.services.document_writer.write_document`.

## Dependencias inversas

- [[python/app/chat_runtime|app/chat_runtime.py]]: depende de este archivo vía `app.tools.create_document.CREATE_DOCUMENT_SYSTEM_PROMPT`, `app.tools.create_document.build_create_document_request`, `app.tools.create_document.create_document_tool`.
- [[python/app/main|app/main.py]]: depende de este archivo vía `app.tools.create_document.create_document_tool`.
- [[python/tests/test_create_document_tool|tests/test_create_document_tool.py]]: depende de este archivo vía `app.tools.create_document.create_document_tool`.

## Imports externos observados

- Paquetes o módulos externos detectados: `collections`, `pydantic`, `typing`

## Relación dentro del sistema

- Su relación operativa exacta requiere contexto adicional del flujo donde se invoca.

## Observaciones

- Sin observaciones adicionales relevantes a partir del análisis estático actual.

## Relacionado

- [[python/app/tools/INDEX]]
- [[RUNTIME_FLOW]]
- [[GLOSSARY]]
