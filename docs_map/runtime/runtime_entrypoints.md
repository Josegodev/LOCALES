# Runtime y puntos de arranque

## FastAPI productivo

- Modulo: `app/main.py`.
- App object: `app = FastAPI(title="Local LLM Gateway")`.
- Endpoints: `/health`, `/documents`, `/chat`.
- Arranque esperado: NO_VERIFICADO; probablemente `uvicorn app.main:app`, pero no hay script raiz que lo declare.

## Telegram

- Script: `run_telegram.py`.
- Requiere `.env` con `TELEGRAM_BOT_TOKEN`.
- Bucle infinito con `getUpdates` y `sendMessage`.

## DB API experimental

- Modulo: `DB/api_server.py`.
- Arranque esperado: NO_VERIFICADO; por imports bare debe ejecutarse con cwd/import path compatible con `DB`.

## Chunks API

- Modulo: `DB/chunks/api.py`.
- Arranque esperado: NO_VERIFICADO; por imports bare debe ejecutarse desde `DB/chunks` o con path ajustado.

## llm_lab

- Modulo: `llm_lab/api.py`.
- Dependencias declaradas en `llm_lab/requirements.txt`.
- Es paquete Python con imports relativos, por tanto debe arrancarse como modulo de paquete.

## Validacion de runtime estatica

- `py_compile` falla por `DB/validator.py`.
- El resto no queda validado como arranque de servicio, solo como parseo/compilacion parcial hasta el primer error.
