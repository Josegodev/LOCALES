# LOCALES / NúcleoChat

`LOCALES` es un gateway de chat LLM construido con `FastAPI`.

Estado actual:

- fase: `HARDENING`
- contrato público activo: `POST /chat`
- proveedores compatibles: `Ollama` y `OpenAI`
- retrieval compatible: `RAG local (SQLite)` y `RAG remoto`
- frontend web activo
- comando de herramienta activo: `/creardoc`

Este repositorio no está en fase de expansión de arquitectura. El objetivo actual es reducir acoplamiento, cerrar contratos, mejorar determinismo y endurecer validación, errores y observabilidad mínima.

## Qué hace el sistema

Flujo principal:

`frontend -> POST /chat -> FastAPI -> retrieval -> provider/model -> ChatResponse`

Capacidades activas:

- chat normal con o sin RAG
- selección de proveedor y modelo
- safe refusal cuando no hay evidencia documental suficiente
- persistencia de runs de chat
- trazas con `trace_id`
- endpoints de métricas y runs para frontend/evals
- creación de documentos Markdown mediante `/creardoc`

## Estado real del código

El sistema tiene una mezcla de piezas cercanas a producción y piezas todavía de hardening.

Más cerca de producción:

- `app/schemas.py`: contratos tipados de `ChatRequest` y `ChatResponse`
- `app/auth.py`: validación explícita de acceso
- `app/llm_errors.py`: errores tipados comunes
- `app/observability/chat_runs.py`: persistencia y normalización de runs
- `app/adapters/ollama_client.py` y `app/adapters/openai_client.py`: integración separada por proveedor

Todavía en transición / hardening:

- `app/chat_runtime.py`: sigue siendo el orquestador principal y aún concentra bastante lógica
- persistencia local por ficheros para runs
- escritura local de documentos en `outputs/documents/`
- diferencias de observabilidad entre Ollama y OpenAI

## Refactor interno ya realizado

No se ha cambiado el contrato público de `/chat`, pero sí se ha reducido acoplamiento interno.

### Contrato público preservado

Se mantienen sin cambios:

- `POST /chat`
- `ChatRequest`
- `ChatResponse`
- `trace_id`
- `retrieval_status`
- `answer_mode`
- `evidence_used`
- `fallback_used`
- `warnings`
- compatibilidad con Ollama y OpenAI
- compatibilidad con RAG local y remoto
- persistencia de runs con `save_chat_run`
- comando `/creardoc`
- endpoints existentes consumidos por frontend

### Nueva estructura interna de chat

```text
app/chat/
  __init__.py
  dependencies.py
  service.py
  retrieval.py
  fallback.py
  response_builder.py
```

Responsabilidades actuales:

- `app/chat/dependencies.py`
  - define `ChatDependencies`
  - agrupa dependencias explícitas del flujo de chat
  - elimina la necesidad de mutar globals desde `app/main.py`

- `app/chat/service.py`
  - define `ChatService`
  - actúa como fachada fina de compatibilidad
  - delega en el runtime existente

- `app/chat/retrieval.py`
  - encapsula la fase de retrieval
  - soporta RAG local y remoto
  - devuelve `RetrievalResult`
  - preserva `retrieval_status`, `chunk_ids`, `document_ids`, `source_filenames` y warnings

- `app/chat/fallback.py`
  - encapsula safe refusal y normalización de fallback
  - decide `answer_mode` para casos documentales, estándar o sin evidencia

- `app/chat/response_builder.py`
  - construye el `ChatResponse` final
  - preserva métricas visibles y warnings públicos

- `app/chat_runtime.py`
  - sigue siendo el orquestador temporal
  - aún contiene generación LLM, tool `/creardoc`, persistencia, logging y manejo principal de errores

## Arquitectura actual

```text
Frontend
  -> FastAPI (`app/main.py`)
  -> ChatService (`app/chat/service.py`)
  -> chat_runtime (`app/chat_runtime.py`)
      -> retrieval (`app/chat/retrieval.py`)
      -> fallback (`app/chat/fallback.py`)
      -> response_builder (`app/chat/response_builder.py`)
      -> llm_client / adapters
      -> document_context (SQLite) o rag_client (HTTP)
      -> create_document_tool
      -> observability / save_chat_run
```

Piezas principales:

- `app/main.py`
  - gateway FastAPI
  - CORS
  - auth
  - construcción explícita de `ChatDependencies` y `ChatService`

- `app/chat_runtime.py`
  - orquestación de chat
  - no debe considerarse todavía completamente modular

- `DB/chunks/document_context.py`
  - motor RAG local sobre SQLite

- `app/rag_client.py`
  - cliente del RAG remoto

- `app/tools/create_document.py`
  - herramienta para generar y guardar documentos

## Endpoints activos

Endpoints principales:

- `GET /health`
- `GET /`
- `POST /chat`
- `GET /api/models/chat`
- `GET /api/chat/options`

Endpoints de trazas y runs:

- `GET /api/traces/chat`
- `POST /api/traces/chat/reset`
- `GET /api/chat/runs`
- `GET /api/chat-runs`
- `GET /api/chat-runs/stats`
- `GET /api/chat-runs/{trace_id}`

Endpoints de evals y métricas:

- `GET /api/evals/chat`
- `GET /api/evals/runs`
- `POST /api/evals/chat/run`
- `GET /api/runs`
- `GET /api/runs/summary`
- `GET /api/runs/timeseries`
- `GET /api/runs/operational-stats`
- `GET /api/runs/by-model/{model_name}`

Nota importante:

- hoy conviven `GET /api/chat/runs` y `GET /api/chat-runs`
- esto mantiene compatibilidad, pero es una zona de drift que conviene vigilar

## Configuración mínima

Ejemplo para entorno local:

```env
APP_ENV=local
BACKEND_BASE_URL=http://127.0.0.1:8000
CHAT_AUTH_MODE=local_open
CHAT_RUNS_PATH=CHAT_RUNS
OLLAMA_BASE_URL=http://127.0.0.1:11434
USE_REMOTE_RAG=false
DOCUMENTS_DB_PATH=/home/jose-gonzalez-oliva/LOCALES/DB/chunks/documents.sqlite
```

Opcional:

```env
JOSE_DEV_TOKEN=change_me
OPENAI_API_KEY=...
RAG_SERVICE_URL=http://127.0.0.1:9000
FRONTEND_ALLOWED_ORIGINS=http://127.0.0.1:3000,http://localhost:3000
```

## Advertencia de seguridad

`CRÍTICO`

- `CHAT_AUTH_MODE=local_open` sirve para local, pero es peligroso si expones el backend por túnel o red pública
- no publiques la instancia con esa configuración
- si usas túneles, configura auth y revisa CORS de forma explícita

Riesgos operativos relevantes:

- CORS abierto o mal alineado con frontend/túneles
- escritura local de documentos y runs
- diferencias de métricas entre Ollama local y OpenAI API
- runtime todavía parcialmente monolítico en `app/chat_runtime.py`

## Ejecutar

Backend:

```bash
cd /home/jose-gonzalez-oliva/LOCALES
source .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Frontend:

```bash
python -m http.server 3000 --directory frontend
```

## Probar manualmente

Health:

```bash
curl http://127.0.0.1:8000/health
```

Chat:

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"hola","provider":"ollama","model":"granite4.1:8b","use_rag":true}'
```

Runs y métricas:

```bash
curl http://127.0.0.1:8000/api/runs?limit=10
curl http://127.0.0.1:8000/api/runs/summary
curl http://127.0.0.1:8000/api/runs/timeseries
curl http://127.0.0.1:8000/api/runs/operational-stats
```

Cada llamada real a `POST /chat` intenta persistir un run.
Si la escritura del run falla, la respuesta del chat debe seguir devolviéndose.

## Tests

Tests puros añadidos para el refactor interno:

- `tests/test_chat_service.py`
- `tests/test_chat_retrieval.py`
- `tests/test_chat_fallback.py`
- `tests/test_chat_response_builder.py`

Otros tests relevantes:

- `tests/test_chat_only_runtime.py`
- `tests/test_dev_token_auth.py`
- `tests/test_remote_rag_service.py`
- `tests/test_chat_run_observability.py`
- `tests/test_retrieval_path_consistency.py`

Compilación sintáctica mínima:

```bash
python3 -m py_compile \
  app/main.py \
  app/chat_runtime.py \
  app/chat/dependencies.py \
  app/chat/service.py \
  app/chat/retrieval.py \
  app/chat/fallback.py \
  app/chat/response_builder.py
```

Tests puros del refactor:

```bash
python3 -m unittest \
  tests.test_chat_service \
  tests.test_chat_retrieval \
  tests.test_chat_fallback \
  tests.test_chat_response_builder
```

Si los tests no arrancan en tu entorno, revisa primero dependencias base:

- `pydantic`
- `pydantic-settings`
- `fastapi`

Archivo de apoyo para entorno de desarrollo:

- `requirements.txt`
- `requirements-dev.txt`

## Limitaciones conocidas

Esto es importante para leer el repositorio sin autoengañarse:

- `app/chat_runtime.py` aún no está completamente desacoplado
- la generación LLM sigue dentro del runtime principal
- la persistencia sigue siendo local-first
- el contrato visible de `ChatResponse` no expone todos los detalles internos del fallback
- OpenAI y Ollama no exponen la misma riqueza de métricas

## Qué no tocar todavía

En esta fase es prematuro reescribir:

- el motor RAG de `DB/chunks/document_context.py`
- el esquema SQL de `DB/schemas/`
- el frontend sólo para seguir el refactor interno
- una nueva arquitectura de colas, workers o frameworks

## Documentos de referencia

- `analysis_results.md`
- `docs/contracts/chat_runtime_refactor_contract.md`
- `docs/remote_rag_service.md`
- `docs/archive/telegram_legacy_runtime.md`
