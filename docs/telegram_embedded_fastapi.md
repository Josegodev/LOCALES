# Telegram embebido en FastAPI

El modo recomendado es ejecutar Telegram dentro del mismo proceso FastAPI. Mantiene el runtime actual: RAG local por `DOCUMENTS_DB_PATH`, modelos locales por `OLLAMA_BASE_URL` y FastAPI escuchando para la LAN.

## Arranque recomendado

```bash
cd /home/jose-gonzalez-oliva/LOCALES
source .venv/bin/activate

export BACKEND_URL=http://127.0.0.1:8000
export OLLAMA_BASE_URL=http://127.0.0.1:11434
export USE_REMOTE_RAG=false
export DOCUMENTS_DB_PATH=/home/jose-gonzalez-oliva/LOCALES/DB/chunks/documents.sqlite

export TELEGRAM_ENABLED=true
export TELEGRAM_BOT_TOKEN="TU_TOKEN_AQUI"
export TELEGRAM_DEFAULT_MODEL="granite4.1:8b"
export TELEGRAM_DEFAULT_TEMPERATURE="0.2"
export TELEGRAM_DEFAULT_RAG_ENABLED=true

uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Control HTTP

La consola frontend llama al Backend API configurado por el usuario y usa:

- `GET /telegram/status`
- `GET /telegram/config`
- `POST /telegram/config`
- `POST /telegram/start`
- `POST /telegram/stop`

`TELEGRAM_BOT_TOKEN` no se devuelve en status ni config. Solo se expone `token_configured`.

## Advertencias

- No usar `--reload` con Telegram embebido.
- No usar varios workers.
- Riesgo principal: polling duplicado contra Telegram si hay otro proceso usando el mismo token.
- `scripts/run_telegram.py` queda como runner standalone legacy/opcional.

## Modo desactivado

Si `TELEGRAM_ENABLED=false` o no esta definido, FastAPI arranca normal y Telegram queda parado. Si `TELEGRAM_BOT_TOKEN` esta definido, puede arrancarse manualmente con `POST /telegram/start`.
