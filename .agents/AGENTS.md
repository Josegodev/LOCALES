# AGENTS.md

## Proyecto

LOCALES / NúcleoChat es un gateway LLM local con FastAPI, frontend estático, RAG SQLite, soporte Ollama/OpenAI, trazabilidad y evaluación.

## Reglas de trabajo

* No modificar lógica de negocio salvo que la tarea lo pida explícitamente.
* No romper los contratos existentes de `/chat`, `/health`, `/api/models/chat`, `/api/chat/options`, `/api/chat-runs`, `/api/evals` y `/api/traces`.
* Mantener compatibilidad con desarrollo local en Linux.
* No introducir secretos en el repositorio.
* No hardcodear rutas absolutas del usuario.
* Preferir configuración vía variables de entorno.
* Mantener logs por stdout.
* Preservar trazabilidad: trace_id, latencia, tokens, retrieval_status, fallback_used y errores.
* Tratar Ollama como servicio externo configurable, no como dependencia obligatoria dentro de Docker.
* En modo dev, priorizar autoreload, bind mounts y comandos simples.
* Antes de cambios grandes, ejecutar o proponer tests/checks mínimos.

## Docker dev

El objetivo del entorno Docker dev es reproducibilidad local, no producción.
Debe permitir levantar frontend, backend y rag_service con docker compose.
Ollama queda fuera de Docker inicialmente y se accede desde los contenedores mediante host.docker.internal:11434.
