# Despliegue local

## Estado actual entendido

El repositorio soporta ejecución local principalmente del backend `FastAPI`, con:

- proveedor local `Ollama`;
- proveedor gestionado `OpenAI`;
- RAG local por SQLite o remoto por servicio HTTP;
- frontend estático separado;
- persistencia local de runs y documentos.

## Arranque del backend principal

### Comando verificado en el repo

Detectado en `README.md`, `evals/README.md` y `Dockerfile`:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Puerto detectado

- Backend principal: `8000`

## Arranque del servicio RAG remoto

Comando documentado en `docs/remote_rag_service.md`:

```bash
export DOCUMENTS_DB_PATH=DB/chunks/documents.sqlite
python3 -m uvicorn rag_service.main:app --host 0.0.0.0 --port 9000
```

### Puerto detectado

- Servicio RAG remoto: `9000`

## Variables de entorno detectadas

Variables principales observadas en `app/config.py` y `.env.example`:

- `APP_ENV`
- `FRONTEND_ALLOWED_ORIGINS`
- `BACKEND_URL`
- `BACKEND_BASE_URL`
- `OLLAMA_BASE_URL`
- `OLLAMA_MODEL`
- `OLLAMA_TIMEOUT_SECONDS`
- `LLM_TIMEOUT_SECONDS`
- `OPENAI_API_KEY`
- `DOCUMENTS_DB_PATH`
- `USE_REMOTE_RAG`
- `RAG_SERVICE_URL`
- `RAG_TIMEOUT_SECONDS`
- `RAG_TOP_K`
- `CHAT_RUNS_PATH`
- `OPERATION_TIMEOUT_MS`
- `JOSE_DEV_TOKEN`
- `CHAT_AUTH_MODE`

## Healthchecks detectados

### Backend principal

- `GET /health`

### Servicio RAG remoto

- `GET /health`
- `GET /rag/health`

## Persistencia local observada

- Runs operativos: `CHAT_RUNS/`
- Traces JSONL legacy/paralelas: `data/chat_traces.jsonl`
- Evals: `evals/runs/`
- Documentos creados por tool: `outputs/documents/`
- Base documental RAG: `DB/chunks/documents.sqlite`

## Frontend local

El frontend detectado es estático:

- `frontend/index.html`
- `frontend/app.js`
- `frontend/api-client.js`
- `frontend/runtime-config.js`

No se ha detectado `package.json`, así que no se puede afirmar aquí un comando de build/dev server propio. Estado: `pendiente de confirmar`.

## Docker

### Archivos detectados

- `Dockerfile`
- `docker-compose.yml`

### Lo que sí se puede afirmar

- La imagen ejecuta `uvicorn app.main:app --host 0.0.0.0 --port 8000`.
- `docker-compose.yml` publica `8000:8000`.
- `docker-compose.yml` monta:
  - `./logs:/app/logs`
  - `./DB:/app/DB`
- `docker-compose.yml` fuerza `OLLAMA_BASE_URL=http://host.docker.internal:11434`.

### Lo que queda pendiente de confirmar

- comando exacto de ejecución con Docker/Compose dentro del flujo habitual del repo;
- si el despliegue containerizado se usa de verdad o solo como apoyo local.

## Riesgos de despliegue detectados

### Autenticación abierta en local

- `CHAT_AUTH_MODE=local_open` es útil en desarrollo.
- Es peligroso si el backend se expone fuera de máquina o LAN controlada.

### Drift en ruta de runs

- `.env.example` usa `CHAT_RUNS_PATH=data/chat_runs.jsonl`.
- La implementación actual persiste y carga runs como directorio con archivos JSON.

### Dependencia implícita de `DB/` en Docker

- `Dockerfile` copia `app/`, pero no copia `DB/`.
- El runtime importa `DB.chunks.document_context`.
- En `docker-compose.yml` esto se compensa con un volumen `./DB:/app/DB`.
- Fuera de compose, la imagen por sí sola podría no tener todo lo necesario.

### Dependencia externa de Ollama o OpenAI

- Para `ollama`, el servicio local debe responder en `OLLAMA_BASE_URL`.
- Para `openai`, hace falta `OPENAI_API_KEY`.

## Validación local mínima sugerida

Comprobaciones respaldadas por el repo:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:9000/rag/health
python -m pytest -q
```

## Conclusión

El despliegue local principal sí está razonablemente definido para backend y RAG remoto. El despliegue exacto del frontend y el uso real de Docker quedan parcialmente `pendientes de confirmar`.

## Relacionado

- [[README]]
- [[OBSERVABILITY]]
- [[TECH_DEBT_AND_RISKS]]
- [[GLOSSARY]]
