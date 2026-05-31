# tests/test_chat_fallback.py

## Rol

Archivo de pruebas que valida contratos o regresiones del sistema.

## Identidad técnica

- Ruta real: `tests/test_chat_fallback.py`
- Tipo: `test`
- Ámbito: `suite de pruebas`
- Módulo lógico: `tests.test_chat_fallback`

## Símbolos principales

- Clases: `ChatFallbackTests`

## Dependencias internas directas

- [[python/app/chat/fallback|app/chat/fallback.py]]: importa `app.chat.fallback.ANSWER_MODE_DOCUMENTARY`, `app.chat.fallback.ANSWER_MODE_SAFE_REFUSAL`, `app.chat.fallback.build_safe_refusal_chat_response`, `app.chat.fallback.fallback_reason_from_state`, `app.chat.fallback.fallback_used_from_state`, `app.chat.fallback.finalize_rag_answer`.
- [[python/app/chat/retrieval|app/chat/retrieval.py]]: importa `app.chat.retrieval.NO_EVIDENCE_MARKER`.

## Dependencias inversas

- No se han detectado dependencias internas inversas dentro del inventario analizado.

## Imports externos observados

- Paquetes o módulos externos detectados: `unittest`

## Relación dentro del sistema

- Participa en la validación automática del comportamiento del sistema.

## Observaciones

- La descripción funcional detallada se debe contrastar con el nombre del test y sus assertions.

## Relacionado

- [[python/tests/INDEX]]
- [[TECH_DEBT_AND_RISKS]]
- [[GLOSSARY]]
