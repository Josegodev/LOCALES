# Mapa de componentes

## Criterio

La tabla siguiente resume rutas reales detectadas en el repositorio. Cuando una responsabilidad no queda explícita por código o README, se marca como `inferencia basada en nombres/rutas`.

| Ruta | Tipo | Responsabilidad observada | Entradas | Salidas | Dependencias principales | Riesgo de acoplamiento | Observaciones |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `app/` | app | Backend principal `FastAPI` y runtime de chat. | HTTP JSON, settings, SQLite, LLMs | JSON API, logs, runs, documentos | `FastAPI`, `pydantic`, `requests`, `DB/chunks` | Alto | Núcleo operativo actual. |
| `app/main.py` | módulo | Construcción de app, CORS e inyección de routers/dependencias. | Settings, imports de app y DB | App ASGI | `app/api`, `app/chat`, `DB.chunks.document_context` | Alto | Gateway fino, pero acoplado a retrieval concreto. |
| `app/api/` | módulo | Routers HTTP de chat, traces, runs, evals y salud. | Requests HTTP | Responses JSON | `app.main` vía runtime bridge, auth, schemas | Medio | Capa HTTP ya separada. |
| `app/chat_runtime.py` | módulo | Orquestación principal de `/chat`. | `ChatRequest`, settings, retrieval, LLM, tool | `ChatResponse`, errores HTTP, runs persistidos | `app/chat/*`, `app/llm_client`, `app/observability`, `DB/chunks` | Alto | Punto más monolítico. |
| `app/chat/` | módulo | Piezas extraídas del runtime: retrieval, fallback, response builder, service. | `ChatRequest`, contextos, dependencias | DTOs internos y `ChatResponse` | `app/schemas`, `DB/chunks` | Medio | Dirección correcta de hardening. |
| `app/adapters/` | módulo | Adaptadores por proveedor LLM. | Prompt, config de modelo | Payload de generación | Ollama HTTP, OpenAI SDK | Medio | Separación correcta por proveedor. |
| `app/llm_client.py` | módulo | Resolución de proveedor/modelo y dispatch al adaptador. | `provider`, `model`, prompt | Resultado normalizado de generación | `app/adapters/*` | Medio | Cierra parte del contrato de compatibilidad. |
| `app/rag_client.py` | módulo | Cliente de RAG remoto con degradación controlada. | Query, top_k, filtros, trace_id | Payload de retrieval | `requests`, `rag_service` | Medio | Devuelve `NO_EVIDENCE_FOR_ANSWER` ante errores remotos. |
| `rag_service/` | app | Servicio HTTP para retrieval remoto. | JSON `POST /rag/query` | JSON de retrieval | `FastAPI`, `DB/chunks/document_context.py` | Medio | Reutiliza el mismo motor local. |
| `DB/chunks/` | datos | Corpus, SQLite y scripts de ingest/RAG local. | PDFs, Markdown, consultas | `documents.sqlite`, chunks, prompts con contexto | `sqlite3`, ficheros PDF/MD | Alto | Base documental del RAG principal. |
| `DB/chunks/document_context.py` | módulo | Ranking, intención documental y construcción de prompt RAG. | Query, allowlist, contexto activo | Contexto, chunks, status | `sqlite3`, `documents.sqlite` | Alto | Contrato crítico entre retrieval y runtime. |
| `DB/` | otro | Laboratorio de persistencia LM Studio separado del runtime principal. | CLI, config, SQLite | `registry.sqlite`, `raw.sqlite`, `memory.sqlite` | `sqlite3`, LM Studio | Bajo | No es el backend de `/chat`. |
| `DB/approve_memory.py` | script | Aprobación manual de memoria persistente. | `slug`, `output-id`, texto | Inserciones en `memory.sqlite` | `DB/db_store.py` | Bajo | Flujo de laboratorio, no integrado con `/chat`. |
| `llm_lab/` | otro | Laboratorio experimental aislado para validar comportamiento de modelos. | HTTP local, variables de entorno | Trazas en `llm_lab/artifacts` | `FastAPI`, proveedor mock/Ollama/LM Studio | Bajo | Aislado de `app/` según su README. |
| `frontend/` | frontend | UI estática para chat, runs y métricas. | Navegador, `runtime-config.js`, backend HTTP | Peticiones a API, render HTML | `fetch`, backend `FastAPI` | Medio | No se detecta `package.json`; parece despliegue estático. |
| `frontend/api-client.js` | frontend | Cliente HTTP con timeout, auth y validación de URL base. | Base URL, auth token, paths | `fetch` normalizado | Browser APIs | Medio | Gestiona errores de configuración y timeout. |
| `scripts/` | script | Utilidades de eval, auditoría e ingest. | CLI, archivos, backend | Informes, runs, SQLite audit | `pytest`, `requests`, `sqlite3` | Bajo | Soporte operativo y de hardening. |
| `scripts/run_chat_evals.py` | script | Runner CLI de evals del contrato `/chat`. | Casos, baseline, backend URL | JSON en `evals/runs/` | `app.chat_eval_runner`, backend HTTP | Medio | Reutiliza el runner interno. |
| `scripts/audit_documents_db.py` | script | Auditoría de base documental. | Ruta a SQLite | JSON de estado del corpus | `sqlite3`, `app.config` | Bajo | Útil para salud de RAG. |
| `scripts/ingest_nucleo_md.py` | script | Ingesta Markdown externa a SQLite. | Árbol `*.md`, `documents.sqlite` | Documentos y chunks | `sqlite3`, filesystem | Medio | Tiene una ruta fija a `NUCLEO/docs`; revisar manualmente. |
| `tests/` | test | Cobertura de contratos, rutas, retrieval, observabilidad y frontend estático. | Código y fixtures | Resultados `pytest` | `pytest`, `unittest`, `TestClient` | Bajo | Buena cobertura de hardening. |
| `evals/` | datos | Casos, baseline y runs de evaluación. | JSON de casos y baseline | JSON de runs | `scripts/run_chat_evals.py`, endpoints eval | Bajo | Separado de los chat runs operativos. |
| `CHAT_RUNS/` | datos | Persistencia actual de runs de chat por archivo JSON. | Payloads de ejecución | Archivos `*.json` | `app/observability/chat_runs.py` | Medio | Fuente principal para stats operativas. |
| `data/` | datos | Artefactos legacy o paralelos de trazas/runs JSONL. | Persistencia local | `chat_runs.jsonl`, `chat_traces.jsonl` | `app/observability/chat_trace.py` | Medio | Posible drift con `CHAT_RUNS/`. |
| `outputs/documents/` | datos | Salida de la tool `/creardoc`. | Contenido Markdown generado | Archivos `.md` | `app/services/document_writer.py` | Bajo | Escritura local, útil para auditoría. |
| `docker-compose.yml` | configuración | Arranque containerizado del backend principal. | `.env`, Docker build, bind mounts | Contenedor `locales-api` | `Dockerfile`, host Ollama, volumen `DB` | Medio | No documenta explícitamente el comando de arranque. |
| `Dockerfile` | configuración | Imagen mínima para `uvicorn app.main:app`. | `requirements.txt`, `app/` | Imagen Docker | Python 3.12 slim | Alto | No copia `DB/`; depende del volumen al ejecutar con compose. |
| `.env.example` | configuración | Variables de entorno de referencia. | N/A | Configuración ejemplo | `app/config.py` | Medio | Contiene campos actuales y algunos legados. |
| `docs/` | documentación | Documentación técnica operativa. | Markdown | Markdown | Repo real | Bajo | Incluye documentos previos y los nuevos. |

## Rutas especialmente relevantes

- Runtime principal: `app/chat_runtime.py`
- Contratos públicos: `app/schemas.py`
- Retrieval local: `DB/chunks/document_context.py`
- Retrieval remoto: `rag_service/main.py`
- Persistencia de runs: `app/observability/chat_runs.py`
- Métricas y stats: `app/evals/metrics.py`, `app/chat_runs/metrics.py`

## CI/CD

No se ha detectado:

- `.github/workflows/`
- pipeline declarada de CI/CD
- configuración equivalente visible en el árbol inspeccionado

Conclusión: `pendiente de confirmar` si la automatización vive fuera del repo.

## Relacionado

- [[README]]
- [[ARCHITECTURE]]
- [[python/INDEX]]
- [[GLOSSARY]]
