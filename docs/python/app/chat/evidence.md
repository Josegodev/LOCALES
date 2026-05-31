# app/chat/evidence.py

## Rol

Módulo interno del runtime de chat extraído para reducir acoplamiento.

## Identidad técnica

- Ruta real: `app/chat/evidence.py`
- Tipo: `chat_component`
- Ámbito: `backend principal`
- Módulo lógico: `app.chat.evidence`

## Símbolos principales

- Funciones: `normalize_source_filename`, `extract_chunk_source_filename`, `extract_chunk_response_data`, `evidence_used_from_payload`

## Dependencias internas directas

- [[python/app/chat/retrieval|app/chat/retrieval.py]]: importa `app.chat.retrieval._extract_chunk_response_data`, `app.chat.retrieval._extract_chunk_source_filename`, `app.chat.retrieval._normalize_source_filename`.

## Dependencias inversas

- [[python/app/chat_runtime|app/chat_runtime.py]]: depende de este archivo vía `app.chat.evidence.evidence_used_from_payload`, `app.chat.evidence.extract_chunk_response_data`, `app.chat.evidence.extract_chunk_source_filename`, `app.chat.evidence.normalize_source_filename`.

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
