# LOCALES distributed RAG over LAN

## 1. Purpose

This mode runs LOCALES as a distributed LAN system.

- Linux owns the RAG corpus: `documents.sqlite`, PDFs, markdown files and chunks.
- Linux owns model inference through Ollama.
- Windows can run the FastAPI chat service.
- FastAPI on Windows calls the Linux RAG Service over HTTP.
- This is useful for learning distributed AI and MLOps operations without moving corpus ownership away from Linux.

The important contract is simple: Windows consumes evidence through HTTP. It should not read SQLite or PDF files directly over Samba at runtime.

## 2. Architecture

Distributed LAN mode:

```text
Telegram bot Linux
  -> FastAPI Windows :8000
      -> RAG Service Linux :9000
          -> documents.sqlite / PDFs / chunks Linux
      -> Ollama Linux :11434
```

Alternative simple all-Linux mode:

```text
Telegram bot Linux
  -> FastAPI Linux :8000
      -> local RAG SQLite
      -> Ollama Linux :11434
```

Use distributed LAN mode when you want to learn and control service boundaries. Use all-Linux mode when you want the simplest operation.

## 3. Services and ports

| Service | Host | Port | Purpose |
| --- | --- | --- | --- |
| Ollama | Linux | `11434` | Model inference |
| RAG Service | Linux | `9000` | Retrieval and evidence API |
| FastAPI Chat | Windows or Linux | `8000` | `/chat` API |
| Telegram bot | Linux | No inbound port | Polls Telegram and calls FastAPI |
| Samba | Linux | Optional | File administration only; not recommended for runtime SQLite/PDF reads |

## 4. Environment variables

Linux RAG Service:

```env
DOCUMENTS_DB_PATH=/home/jose-gonzalez-oliva/LOCALES/DB/chunks/documents.sqlite
RAG_TOP_K=5
```

`RAG_TOP_K` is optional. It controls the default number of chunks returned when a request does not provide `top_k`.

Windows FastAPI using remote RAG:

```env
USE_REMOTE_RAG=true
RAG_SERVICE_URL=http://192.168.1.51:9000
RAG_TIMEOUT_SECONDS=10
OLLAMA_BASE_URL=http://192.168.1.51:11434
BACKEND_URL=http://192.168.1.20:8000
```

Use `BACKEND_URL=http://192.168.1.20:8000` when the Telegram bot points to the Windows FastAPI service.

Linux all-in-one FastAPI:

```env
USE_REMOTE_RAG=false
DOCUMENTS_DB_PATH=/home/jose-gonzalez-oliva/LOCALES/DB/chunks/documents.sqlite
OLLAMA_BASE_URL=http://127.0.0.1:11434
BACKEND_URL=http://127.0.0.1:8000
```

Use `BACKEND_URL=http://127.0.0.1:8000` when the Telegram bot runs on the same Linux host as FastAPI.

## 5. Start commands

Linux: start Ollama.

```bash
ollama serve
```

If Ollama is already installed as a service, it may already be running. In that case, do not start a second copy.

Linux: start RAG Service.

```bash
cd /home/jose-gonzalez-oliva/LOCALES
.venv/bin/python -m uvicorn rag_service.main:app --host 0.0.0.0 --port 9000 --log-level debug
```

Windows: start FastAPI using remote RAG.

```powershell
cd C:\Users\joseg\proyectos\LOCALES
.\.venv\Scripts\Activate.ps1
$env:USE_REMOTE_RAG = "true"
$env:RAG_SERVICE_URL = "http://192.168.1.51:9000"
$env:RAG_TIMEOUT_SECONDS = "10"
$env:OLLAMA_BASE_URL = "http://192.168.1.51:11434"
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Linux: optional all-in-one FastAPI.

```bash
cd /home/jose-gonzalez-oliva/LOCALES
source .venv/bin/activate
export USE_REMOTE_RAG=false
export DOCUMENTS_DB_PATH=/home/jose-gonzalez-oliva/LOCALES/DB/chunks/documents.sqlite
export OLLAMA_BASE_URL=http://127.0.0.1:11434
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 6. Health checks

From Linux:

```bash
curl -v --max-time 5 http://127.0.0.1:9000/health
curl -v --max-time 5 http://192.168.1.51:9000/health
curl -v --max-time 5 http://127.0.0.1:9000/rag/health
```

From Windows:

```powershell
curl.exe -v --max-time 5 http://192.168.1.51:9000/health
curl.exe -v --max-time 5 http://192.168.1.51:9000/rag/health
curl.exe -v --max-time 5 http://192.168.1.20:8000/health
```

Expected result: HTTP health endpoints should return quickly. If a command hangs or times out, diagnose networking before changing application code.

## 7. RAG query tests

From Windows to RAG Service:

```powershell
curl.exe -X POST "http://192.168.1.51:9000/rag/query" -H "Content-Type: application/json" -d "{\"query\":\"Que es un transformer?\",\"top_k\":5}"
```

With source filter:

```powershell
curl.exe -X POST "http://192.168.1.51:9000/rag/query" -H "Content-Type: application/json" -d "{\"query\":\"Que es un transformer?\",\"top_k\":5,\"allowed_source_filenames\":[\"Attention is all you need.pdf\"]}"
```

Impossible filter:

```powershell
curl.exe -X POST "http://192.168.1.51:9000/rag/query" -H "Content-Type: application/json" -d "{\"query\":\"Que es un transformer?\",\"top_k\":5,\"allowed_source_filenames\":[\"NO_EXISTE.pdf\"]}"
```

Expected results:

- Valid evidence: `retrieval_status=EVIDENCE_FOUND`, `chunks_found > 0`.
- No evidence: `retrieval_status=NO_EVIDENCE_FOR_ANSWER`, `chunks_found=0`.
- Remote RAG down: FastAPI `/chat` should fallback with warning `RAG_SERVICE_UNAVAILABLE`.

## 8. FastAPI /chat tests

From Windows:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/chat" -H "Content-Type: application/json" -d "{\"message\":\"Que es un transformer?\",\"use_rag\":true}"
```

From Linux to Windows FastAPI:

```bash
curl -X POST "http://192.168.1.20:8000/chat" -H "Content-Type: application/json" -d '{"message":"Que es un transformer?","use_rag":true}'
```

Expected response fields:

- `retrieval_status`
- `evidence_used`
- `fallback_used`
- `chunks_found`
- `warnings`
- source filenames and chunk IDs, if available

## 9. Firewall / LAN checklist

Linux: check the listening port.

```bash
ss -lntp | grep 9000
```

Expected:

```text
0.0.0.0:9000
```

or:

```text
*:9000
```

Bad:

```text
127.0.0.1:9000
```

If the service binds only to `127.0.0.1`, other PCs in the LAN cannot reach it.

Open UFW for the LAN:

```bash
sudo ufw allow from 192.168.1.0/24 to any port 9000 proto tcp
sudo ufw allow from 192.168.1.0/24 to any port 8000 proto tcp
sudo ufw reload
sudo ufw status numbered
```

Windows port test:

```powershell
Test-NetConnection 192.168.1.51 -Port 9000
```

Failure meanings:

- `connection refused`: service is not listening on that port, or it is bound to the wrong address.
- timeout: firewall, routing or network filtering is blocking the connection.
- `/health` works but `/rag/health` hangs: inspect the endpoint implementation and SQLite audit path.
- `/rag/health` works but `/rag/query` fails: inspect retrieval code, corpus contents and query filters.

## 10. Why not use Samba for runtime RAG?

Samba is acceptable for file administration, such as copying PDFs or inspecting generated files.

Do not use Samba as the runtime path for SQLite or PDF reads if avoidable:

- SQLite over network shares can create locking and debugging problems.
- Paths stored inside the database may be Linux paths and invalid from Windows.
- Runtime file access over a share mixes storage ownership with application execution.
- HTTP RAG Service gives a cleaner contract: Windows asks for evidence, Linux reads its own corpus and returns a response.

## 11. Known limitations

- `active_document_id` and `active_document_title` parity may still be pending if it has not been implemented.
- RAG Service currently has no authentication; expose it only on a trusted LAN.
- There is no systemd service yet unless one has already been added outside this document.
- There is no Docker Compose setup yet for this distributed mode.
- SQLite is still local storage; PostgreSQL/pgvector may be a later evolution if corpus size or concurrency grows.

## 12. Recommended operational mode

For simplest operation, run everything on Linux with `USE_REMOTE_RAG=false`.

For distributed learning and control, run RAG Service on Linux and FastAPI on Windows with `USE_REMOTE_RAG=true`.

Windows should not own the RAG corpus in the current architecture. Linux remains the source of truth for `documents.sqlite`, PDFs, markdown files and chunks.
