# app/chat/response_builder.py

## Rol

Módulo interno del runtime de chat extraído para reducir acoplamiento.

## Identidad técnica

- Ruta real: `app/chat/response_builder.py`
- Tipo: `chat_component`
- Ámbito: `backend principal`
- Módulo lógico: `app.chat.response_builder`

## Símbolos principales

- Funciones: `normalize_public_warnings`, `build_chat_response`

## Dependencias internas directas

- [[python/app/schemas|app/schemas.py]]: importa `app.schemas.ChatResponse`.

## Dependencias inversas

- [[python/app/chat/fallback|app/chat/fallback.py]]: depende de este archivo vía `app.chat.response_builder.build_chat_response`.
- [[python/tests/test_chat_response_builder|tests/test_chat_response_builder.py]]: depende de este archivo vía `app.chat.response_builder.build_chat_response`.

## Imports externos observados

- Paquetes o módulos externos detectados: `typing`

## Relación dentro del sistema

- Forma parte del runtime modularizado de chat.

## Observaciones

- Sin observaciones adicionales relevantes a partir del análisis estático actual.

## Relacionado

- [[python/app/chat/INDEX]]
- [[RUNTIME_FLOW]]
- [[GLOSSARY]]
