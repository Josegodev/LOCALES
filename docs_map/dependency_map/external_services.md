# Servicios externos y locales

## Telegram Bot API

- Usado por `run_telegram.py` y `app/telegram_client.py`.
- Base: `https://api.telegram.org/bot{TG_TOKEN}`.
- Endpoints usados: `getUpdates`, `sendMessage`.

## LM Studio

- App productiva: `settings.lmstudio_base_url`, default `http://127.0.0.1:1234/v1`.
- DB API: `DB/config.json` campo `lmstudio_base_url`.
- Chunks API: URL hardcodeada `http://127.0.0.1:1234/v1/chat/completions`.
- llm_lab: default `http://127.0.0.1:1234/v1/chat/completions` si `LLM_LAB_PROVIDER=lmstudio`.

## Ollama

- Solo observado en `llm_lab/model_adapter.py`.
- Default `http://127.0.0.1:11434/api/generate`.

## Riesgo de acoplamiento

- Las URLs estan repetidas en varios sitios. Eso es riesgo de drift: un cambio de puerto/base URL puede dejar partes del sistema apuntando a valores distintos.
