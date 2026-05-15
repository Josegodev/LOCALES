# LOCALES

`LOCALES` funciona en modo chat-only.

Runtime soportado:

`frontend -> POST /chat -> FastAPI -> RAG -> provider/model -> structured JSON`

Telegram ha sido eliminado del runtime activo.
Los evals legacy han sido eliminados.
Los futuros evals deben apuntar directamente a `/chat`.

## Archivos activos

- `app/main.py`
- `app/auth.py`
- `app/llm_client.py`
- `app/rag_client.py`
- `app/observability/chat_runs.py`
- `app/observability/logging.py`
- `DB/chunks/document_context.py`
- `frontend/index.html`
- `frontend/app.js`
- `frontend/styles.css`
- `docs/contracts/chat_runtime_refactor_contract.md`

## Configuración mínima

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
```

Variables que ya no hacen falta para arrancar el backend principal:

```env
TELEGRAM_ENABLED
TELEGRAM_BOT_TOKEN
TELEGRAM_ALLOWED_USER_IDS
TELEGRAM_ALLOWED_CHAT_IDS
```

## Ejecutar

Backend:

```bash
cd /home/jose-gonzalez-oliva/LOCALES
source .venv/bin/activate
export APP_ENV=local
export BACKEND_BASE_URL=http://127.0.0.1:8000
export OLLAMA_BASE_URL=http://127.0.0.1:11434
export USE_REMOTE_RAG=false
export DOCUMENTS_DB_PATH=/home/jose-gonzalez-oliva/LOCALES/DB/chunks/documents.sqlite
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Frontend:

```bash
python -m http.server 3000 --directory frontend
```

## Probar

Comprobaciones HTTP mínimas:

```bash
curl http://127.0.0.1:8000/health
curl -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d '{"message":"hola","provider":"ollama","model":"granite4.1:8b","use_rag":true}'
curl http://127.0.0.1:8000/api/chat/runs?limit=10
bash scripts/run_chat_eval_e2e.sh
```

Cada llamada real a `POST /chat` escribe un JSON independiente en `CHAT_RUNS/`.
Si la escritura del archivo falla, la respuesta del chat sigue devolviendose.

El comando E2E levanta una instancia temporal del backend actual en `127.0.0.1:8011`, ejecuta el endpoint de evals y la apaga al terminar.

Tests mínimos del runtime actual:

```bash
.venv/bin/python -m unittest \
  tests.test_chat_only_runtime \
  tests.test_dev_token_auth \
  tests.test_document_context \
  tests.test_remote_rag_service \
  tests.test_retrieval_path_consistency
```

## Contrato

La fuente de verdad del refactor vive en:

- `docs/contracts/chat_runtime_refactor_contract.md`

Nota histórica mínima:

- `docs/archive/telegram_legacy_runtime.md`

Documentación opcional de RAG remoto:

- `docs/remote_rag_service.md`
