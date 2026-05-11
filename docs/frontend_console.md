# LOCALES frontend console

La consola vive en `frontend/` y es un frontend estatico: `index.html`, `styles.css` y `app.js`.
No lee SQLite, PDFs, chunks ni el runtime de modelos directamente. Solo llama al Backend API configurado en el input.

## Como abrirla en Windows

Desde el repo:

```powershell
cd C:\Users\joseg\proyectos\LOCALES\frontend
python -m http.server 3000
```

Abrir en el navegador local:

```text
http://localhost:3000
```

Backend URL:

```text
Introduce la URL real del Backend API en el input "Backend base URL".
```

## FastAPI Linux requerido

En Linux MSI:

```bash
cd /home/jose-gonzalez-oliva/LOCALES
source .venv/bin/activate
export BACKEND_URL=http://127.0.0.1:8000
export OLLAMA_BASE_URL=http://127.0.0.1:11434
export USE_REMOTE_RAG=false
export DOCUMENTS_DB_PATH=/home/jose-gonzalez-oliva/LOCALES/DB/chunks/documents.sqlite
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Que prueba

- `GET /health` para comprobar conectividad.
- `POST /chat` con `{ "message": "...", "use_rag": true|false }`.
- `GET /telegram/status`, `GET /telegram/config`, `POST /telegram/config`, `POST /telegram/start`, `POST /telegram/stop` para controlar Telegram embebido.
- Muestra `retrieval_status`, `evidence_used`, `fallback_used`, `chunks`, `source_filenames`, `chunk_ids`, `document_ids`, `warnings`, `provider`, `model` y latencia medida por el navegador.

## CORS

FastAPI permite origenes de desarrollo concretos:

- `http://localhost:3000`
- `http://127.0.0.1:3000`
- `http://192.168.1.20:3000`
- `http://localhost:8080`
- `http://127.0.0.1:8080`

No se usa `*`. Si Windows usa otra IP/puerto para servir la consola, hay que anadir ese origen a `FRONTEND_DEV_ORIGINS` en `app/main.py`.

## Limitaciones

- No hay autenticacion; usar solo en LAN confiable.
- La consola no sustituye a `/docs`; es una vista operacional y de aprendizaje.
- El resultado de `/chat` depende de que el runtime de modelos y el RAG local esten disponibles en el backend.
- El modo RAG remoto por LAN existe para experimentos, pero no es el runtime principal recomendado.
