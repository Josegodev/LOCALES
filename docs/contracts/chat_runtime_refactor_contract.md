# Chat Runtime Refactor Contract

## Purpose

NUCLEO se reduce temporalmente a un runtime chat-only porque el unico camino confirmado como operativo con RAG es:

Frontend -> `POST /chat` -> FastAPI -> retrieval RAG -> provider/modelo local -> respuesta estructurada JSON.

El objetivo de esta reduccion es bajar entropia, cerrar contratos y dejar una base reproducible antes de reabrir integraciones legacy.

## Supported runtime path

Frontend
  -> `POST /chat`
  -> FastAPI
  -> RAG retrieval
  -> model/provider call
  -> structured response

Contrato operativo esperado:

- el frontend envia `message` y `use_rag`, y puede enviar `provider`, `model`, `temperature`, `max_tokens`, `top_k` y `trace_id`
- FastAPI valida el request con `ChatRequest`
- el backend ejecuta retrieval local o remoto segun configuracion
- el backend llama al provider/modelo ya soportado
- el backend devuelve `ChatResponse` con metadatos de retrieval, latencia y tokens cuando existen

## Explicitly removed from active runtime

- Telegram bot
- Telegram webhook/polling
- Telegram evals
- old eval frontend/backend paths
- any runtime startup dependency on Telegram

En la practica esto significa:

- `app/main.py` no importa `app.telegram_runtime`
- FastAPI no monta rutas `/telegram/*`
- FastAPI no monta rutas `/api/evals/telegram`
- la observabilidad del flujo principal no lee evals legacy para completar trazas del chat

## Preserved capabilities

- main chat frontend
- `/chat` API
- RAG evidence retrieval
- local model/provider selection where applicable
- structured JSON response
- `trace_id` / `run_id` where available
- basic observability/logging

Capacidades concretas preservadas en `ChatResponse`:

- `trace_id`
- `status`
- `provider`
- `model`
- `temperature`
- `use_rag`
- `answer`
- `latency_ms`
- `retrieval_status`
- `evidence_used`
- `fallback_used`
- `chunk_ids`
- `document_ids`
- `source_filenames`
- `warnings`
- metricas de tokens cuando el provider las entrega

## Future evals direction

Los futuros evals deben apuntar directamente a `/chat`, no a Telegram.

Contrato propuesto para `EvalCase`:

- `id`
- `input`
- `expected_retrieval_status`
- `required_source_filenames`
- `required_chunk_ids` optional
- `forbidden_terms`
- `expected_answer_contains`
- `model`
- `temperature`
- `max_tokens`

Contrato propuesto para `EvalRun`:

- `run_id`
- `trace_id`
- `case_id`
- `input`
- `response`
- `retrieval_status`
- `chunk_ids`
- `document_ids`
- `source_filenames`
- `latency_ms`
- `tokens_input`
- `tokens_output`
- `tokens_total`
- `estimated_cost` optional
- `status`
- `error_code`
- `error_message`

## Chat eval foundation

Cada llamada real a `POST /chat` persiste un artefacto JSON independiente en el directorio configurado por `CHAT_RUNS_DIR` / `CHAT_RUNS_PATH`.

El contrato activo de proyeccion de runs es:

- `GET /api/runs`: listado normalizado de artefactos de run
- `GET /api/runs/summary`: agregados globales y metricas por modelo calculadas en backend
- `GET /api/runs/timeseries`: serie temporal normalizada con `created_at`, `model`, `latency_ms`, `tokens_input`, `tokens_output`, `tokens_total`, `status`, `retrieval_status`, `fallback_used` y `trace_id`
- `GET /api/runs/operational-stats`: benchmark operacional agregado por modelo con latencias, percentiles, tasas, tokens y throughput calculados en backend
- `GET /api/runs/by-model/{model_name}`: runs filtrados por modelo y metricas del modelo

La UI de `frontend/` usa `operational-stats` para los paneles `Operational Benchmark` y `RUNS temperature`. El frontend solo renderiza tablas, tarjetas y barras; no recalcula percentiles, medias, tasas ni desviaciones.

`GET /api/evals/chat` existe ahora solo para compatibilidad y lista trazas recientes del runtime chat-only.

`POST /api/evals/chat/run` ejecuta los chat evals contra el mismo contrato estable de `/chat` y persiste el run en `evals/runs/`.

Esto significa:

- `/api/evals/chat` no ejecuta evals
- `/api/evals/chat` no llama a `POST /chat`
- los casos existen como contrato estatico en `evals/cases/chat_cases.json`
- los baselines existen como contrato estatico en `evals/baselines/chat_baseline.json`
- el eval runner ejecuta casos contra el mismo contrato estable de `/chat`
- los resultados de eval se almacenan separados de las runtime traces

## Non-goals

- do not redesign the full agent runtime
- do not reintroduce Telegram
- do not build distributed architecture
- do not add cloud deployment
- do not add new model providers unless already present
- do not implement new eval dashboard yet

## Acceptance criteria

- backend starts with uvicorn without Telegram env vars
- frontend loads
- frontend can send a message to `/chat`
- `/chat` returns valid JSON
- RAG still retrieves evidence when documents match
- no Telegram import is required during backend startup
- no eval route is required for normal chat
- tests or smoke checks exist for `/health` and `/chat`
- README or docs mention chat-only mode

## Minimal environment

Variables minimas del backend:

- `APP_ENV=local`
- `BACKEND_BASE_URL=http://127.0.0.1:8000`
- `CHAT_AUTH_MODE=local_open`
- `CHAT_RUNS_PATH=CHAT_RUNS`
- `OLLAMA_BASE_URL=http://127.0.0.1:11434`
- `DOCUMENTS_DB_PATH=/home/jose-gonzalez-oliva/LOCALES/DB/chunks/documents.sqlite`
- `USE_REMOTE_RAG=false`

Variables opcionales:

- `JOSE_DEV_TOKEN` si `CHAT_AUTH_MODE=bearer_required`
- `OPENAI_API_KEY` solo si se usa provider OpenAI ya soportado
- `RAG_SERVICE_URL` si `USE_REMOTE_RAG=true`

Variables que ya no son necesarias para arrancar el backend principal:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `TELEGRAM_ENABLED`
- cualquier variable de eval ligada a Telegram
