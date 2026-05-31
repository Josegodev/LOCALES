# app/chat/commands.py

## Rol

Módulo interno del runtime de chat extraído para reducir acoplamiento.

## Identidad técnica

- Ruta real: `app/chat/commands.py`
- Tipo: `chat_component`
- Ámbito: `backend principal`
- Módulo lógico: `app.chat.commands`

## Símbolos principales

- Funciones: `parse_chat_command`

## Dependencias internas directas

- No se han detectado imports internos directos del repositorio.

## Dependencias inversas

- [[python/app/chat_runtime|app/chat_runtime.py]]: depende de este archivo vía `app.chat.commands.CREATE_DOCUMENT_COMMAND`, `app.chat.commands.CREATE_DOCUMENT_PREFIX`, `app.chat.commands.parse_chat_command`.

## Imports externos observados

- No se han detectado imports externos explícitos.

## Relación dentro del sistema

- Forma parte del runtime modularizado de chat.

## Observaciones

- Sin observaciones adicionales relevantes a partir del análisis estático actual.

## Relacionado

- [[python/app/chat/INDEX]]
- [[RUNTIME_FLOW]]
- [[GLOSSARY]]
