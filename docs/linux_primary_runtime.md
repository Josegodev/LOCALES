# LOCALES Linux primary runtime

## 1. Purpose

This is the recommended operational mode for LOCALES right now.

Use Linux as the primary runtime host for:

- Telegram bot
- FastAPI
- local RAG
- Ollama

This keeps the main execution path on one machine and leaves distributed mode as an optional experiment.

## 2. Architecture

```text
Telegram bot Linux
  -> FastAPI Linux :8000
      -> local RAG SQLite
      -> Ollama Linux :11434

Windows:
  -> optional client/dev only
  -> can call http://192.168.1.51:8000/health
```

## 3. Services on Linux

| Service | Port | Purpose |
| --- | --- | --- |
| Ollama | `11434` | Model inference |
| FastAPI LOCALES | `8000` | `/chat` and `/health` |
| Telegram bot | No inbound port | Outbound polling; calls `BACKEND_URL` |
| RAG local | No port | Uses `documents.sqlite` directly |
| RAG Service | `9000` optional | Only for distributed experiment |

## 4. Environment variables for primary mode

Recommended values:

```env
BACKEND_URL=http://127.0.0.1:8000
OLLAMA_BASE_URL=http://127.0.0.1:11434
USE_REMOTE_RAG=false
DOCUMENTS_DB_PATH=/home/jose-gonzalez-oliva/LOCALES/DB/chunks/documents.sqlite
```

Important notes:

- If Windows must call FastAPI on Linux, FastAPI should bind to `0.0.0.0`.
- If Windows must call FastAPI on Linux, UFW should allow port `8000` from the LAN.
- If Telegram runs on the same Linux host, use `BACKEND_URL=http://127.0.0.1:8000`.

## 5. Start commands

Start Ollama:

```bash
ollama serve
```

If Ollama already runs as a service, do not start a second instance.

Start FastAPI:

```bash
cd /home/jose-gonzalez-oliva/LOCALES
source .venv/bin/activate
export BACKEND_URL=http://127.0.0.1:8000
export OLLAMA_BASE_URL=http://127.0.0.1:11434
export USE_REMOTE_RAG=false
export DOCUMENTS_DB_PATH=/home/jose-gonzalez-oliva/LOCALES/DB/chunks/documents.sqlite
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Start Telegram bot:

```bash
cd /home/jose-gonzalez-oliva/LOCALES
source .venv/bin/activate
export BACKEND_URL=http://127.0.0.1:8000
python scripts/run_telegram.py
```

The Telegram script path in this repository is `scripts/run_telegram.py`.

## 6. Health checks

Local Linux:

```bash
curl http://127.0.0.1:8000/health
```

From Windows:

```powershell
curl.exe http://192.168.1.51:8000/health
```

RAG local test:

```bash
curl -X POST "http://127.0.0.1:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message":"Que es un transformer?","use_rag":true}'
```

Expected response fields:

- `retrieval_status`
- `evidence_used`
- `fallback_used`
- `chunks_found`
- `warnings`

## 7. Firewall

Only needed if Windows or another LAN client calls FastAPI on Linux:

```bash
sudo ufw allow from 192.168.1.0/24 to any port 8000 proto tcp
sudo ufw reload
sudo ufw status numbered
```

Important notes:

- There is no need to expose port `9000` unless you use the optional RAG Service.
- There is no need for Samba in the runtime path.

## 8. Why this mode is preferred now

This mode is preferred because it has:

- fewer moving parts
- corpus and retrieval on the same filesystem
- no SQLite over network share
- no Windows/Linux path drift
- easier logs
- easier future `systemd` setup
- enough deployment and observability value without extra distributed failure surface

## 9. Optional distributed mode

Use distributed mode when you want to learn or test service boundaries:

- `docs/distributed_rag_lan.md`
- `docs/remote_rag_service.md`

It is not required for the production local bot path.

## 10. Next hardening steps

- `systemd` unit for FastAPI
- `systemd` unit for Telegram bot
- `systemd` unit for optional RAG Service
- structured logs per request
- `rag_latency_ms`
- `model_latency_ms`
- eval runs after deploy
