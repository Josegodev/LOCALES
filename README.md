# LOCALES

## Propósito

`LOCALES` se ejecuta ahora en modo principal navegador -> FastAPI -> `/chat` -> RAG/modelo, con trazas visibles desde la ventana principal. Telegram queda como adaptador legacy opcional.

El objetivo práctico actual es:

- mantener estable el contrato principal de `/chat`
- ejecutar y revisar trazas/evals desde el frontend principal
- conservar Telegram como legacy reversible, sin formar parte del arranque principal
- responder preguntas sobre un repositorio fijo con herramientas deterministas

## Estado actual

- Frontend principal y `/chat` operativos.
- Trazas de `/chat` consultables en `/api/evals/chat`.
- Bot Telegram conservado como legacy opcional.
- `/repo` experimental para analizar únicamente `REPO_ANALYZER_PATH`.
- Herramientas deterministas para lectura y búsqueda en repositorio.
- Fallback LLM con Ollama para preguntas abiertas de repositorio.
- Trazas ampliadas para el flujo Telegram legacy.

## Componentes principales

| Componente | Ruta | Función |
| --- | --- | --- |
| Frontend principal | `frontend/app.js` | Cliente navegador de `/health`, `/chat` y `/api/evals/chat` |
| FastAPI principal | `app/main.py` | Contrato HTTP principal, auth, `/chat`, `/health` y trazas consultables |
| Trazas `/chat` | `app/observability/chat_trace.py` | Persiste y carga ejecuciones del frontend principal |
| Bot Telegram legacy | `app/services/bot_service.py` | Orquesta mensajes Telegram y persistencia legacy |
| Servicio `/repo` | `app/services/repo_analyzer_service.py` | Valida configuración de `/repo`, ejecuta routing y formatea respuestas |
| Tools deterministas | `app/services/repo_tools.py` | Resuelve lectura de líneas, búsqueda, árbol y localización de archivos |
| Trazas Telegram legacy | `app/observability/telegram_trace.py` | Persiste `trace_id`, metadata y artefactos de ejecución Telegram |
| Guía `/repo` | `docs/repo_analyzer_telegram.md` | Documentación completa del flujo `/repo` |

## Configuración mínima

Variables necesarias para `/repo`:

```env
REPO_ANALYZER_ENABLED=true
REPO_ANALYZER_PATH=/home/jose-gonzalez-oliva/LOCALES
REPO_ANALYZER_MODEL=granite4.1:8b
REPO_ANALYZER_TEMPERATURE=0.2
```

Variables mínimas del runtime principal:

```env
APP_ENV=local
BACKEND_BASE_URL=http://127.0.0.1:8000
CHAT_AUTH_MODE=local_open
OLLAMA_BASE_URL=http://127.0.0.1:11434
USE_REMOTE_RAG=false
DOCUMENTS_DB_PATH=/home/jose-gonzalez-oliva/LOCALES/DB/chunks/documents.sqlite
```

Variables mínimas del bot Telegram legacy:

```env
TELEGRAM_ENABLED=true
TELEGRAM_BOT_TOKEN=...
TELEGRAM_DEFAULT_MODEL=granite4.1:8b
TELEGRAM_DEFAULT_TEMPERATURE=0.2
TELEGRAM_DEFAULT_RAG_ENABLED=true
TELEGRAM_ALLOWED_USER_IDS=123456789
```

Variable mínima adicional para endpoints operacionales protegidos:

```env
JOSE_DEV_TOKEN=change_me
CHAT_AUTH_MODE=local_open
```

## Modo principal recomendado

La ruta operativa recomendada ahora es ejecutar el contrato principal en Linux:

- FastAPI en Linux
- RAG local en Linux usando `documents.sqlite`
- Ollama en Linux
- frontend como cliente web del mismo backend

Telegram ya no forma parte del arranque principal. Windows puede quedarse como máquina de desarrollo o cliente de prueba. Por ejemplo, puede consultar:

```bash
curl http://192.168.1.51:8000/health
```

El modo distribuido por LAN sigue disponible, pero ya no es la ruta por defecto. La razón práctica es reducir superficie de depuración:

- evita problemas de runtime con Samba y SQLite
- evita drift de rutas Windows/Linux
- reduce piezas móviles en producción local
- simplifica logs, arranque y futuras unidades `systemd`

Guía recomendada:

- `docs/linux_primary_runtime.md`

Modo distribuido opcional:

- `docs/distributed_rag_lan.md`
- `docs/remote_rag_service.md`

## Configurar backend remoto en LAN

Si FastAPI corre en otro PC, el bot no debe usar `127.0.0.1`, porque esa IP siempre apunta a la propia máquina donde corre el proceso.

Si bot y API están en la misma máquina:

```env
BACKEND_URL=http://127.0.0.1:8000
```

Configura `BACKEND_URL` en tu `.env`:

```env
BACKEND_URL=http://IP_DEL_PC_API:8000
```

Ejemplo en una red local:

```env
BACKEND_URL=http://IP_WINDOWS:8000
```

El bot y los scripts de eval construirán las rutas a partir de esa base, por ejemplo:

- `http://IP_DEL_PC_API:8000/chat`
- `http://IP_DEL_PC_API:8000/documents`

Si la API corre en Windows y el bot en Linux, una comprobación mínima desde Linux es:

```bash
curl http://IP_WINDOWS:8000/health
```

## Distributed RAG over LAN

LOCALES también puede ejecutarse en modo distribuido dentro de la LAN, pero ese camino es opcional. Úsalo cuando quieras aprender o probar límites de servicio entre Windows y Linux.

Guías:

- `docs/linux_primary_runtime.md`
- `docs/distributed_rag_lan.md`

## Uso rápido

Arranque principal recomendado en Linux:

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

Comando unico de frontend local:

```bash
python -m http.server 3000 --directory frontend
```

Telegram se mantiene como runner standalone legacy/opcional:

```bash
export TELEGRAM_ENABLED=true
export TELEGRAM_BOT_TOKEN="<NO_COMMIT_REAL_TOKEN>"
python scripts/run_telegram.py
```

## Frontend web console

Hay una consola operacional estatica en `frontend/` para usar Windows como cliente del runtime Linux.

```powershell
cd C:\Users\joseg\proyectos\LOCALES\frontend
python -m http.server 3000
```

Abrir:

```text
http://localhost:3000
```

La consola usa `http://127.0.0.1:8000` como valor inicial de `Backend base URL`, permite cambiarlo manualmente y lo recuerda en `localStorage`. Prueba `/health`, `/chat`, `/api/evals/chat` y deja Telegram en secciones legacy separadas. Mas detalle en `docs/frontend_console.md` y `docs/telegram_embedded_fastapi.md`.

Ejemplos de `/repo` en Telegram:

- `/repo línea 14 de config.py`
- `/repo busca REPO_ANALYZER_ENABLED`
- `/repo estructura del repo`
- `/repo Qué riesgos ves en este repo?`

Resumen de comportamiento:

- preguntas exactas usan tools deterministas
- preguntas abiertas usan fallback LLM
- `/repo` no acepta rutas dinámicas desde Telegram

## Verificación

```bash
python3 -m compileall app scripts tests
python3 -m pytest -q
```

## Límites conocidos

- `/repo` no edita archivos.
- `/repo` no ejecuta comandos.
- `/repo` no acepta `repo_path` desde Telegram.
- `/repo` no hace análisis multi-repo.
- El fallback LLM requiere Ollama.
- El fallback LLM depende del workspace `Analyzer`.
- Las reglas de exclusión están duplicadas localmente en `app/services/repo_tools.py`.

## Dev token auth

Los endpoints operacionales del backend requieren ahora:

```text
Authorization: Bearer <JOSE_DEV_TOKEN>
```

Rutas abiertas:

- `/health`
- `/chat` cuando `CHAT_AUTH_MODE=local_open`

Rutas protegidas:

- `/documents`
- `/telegram/*`
- `/api/evals/telegram`

Contrato especifico de `/chat`:

- `CHAT_AUTH_MODE=local_open`: acepta llamadas sin Bearer para frontend local/LAN y registra un warning seguro.
- `CHAT_AUTH_MODE=bearer_required`: exige `Authorization: Bearer <JOSE_DEV_TOKEN>`.
- `CHAT_AUTH_MODE=disabled`: responde `403`.

Contrato de `/api/evals/chat`:

- usa el mismo gate que `/chat`
- expone solo ejecuciones `source=frontend` o `source=chat`
- no mezcla trazas Telegram

El flujo es simple:

- el servidor lee `JOSE_DEV_TOKEN` desde su entorno
- el frontend navegador no guarda ni envia el token operacional
- clientes server-side como Telegram o scripts de eval usan `Authorization: Bearer <JOSE_DEV_TOKEN>` desde entorno mediante el cliente interno

Esto es hardening de desarrollo, no autenticación completa de producción.

## Manual curl tests

Comprobar que `/health` sigue abierto:

```bash
curl http://127.0.0.1:8000/health
```

Comprobar que `/chat` local abierto responde sin token:

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"hola"}'
```

Comprobar que `/chat` con `CHAT_AUTH_MODE=bearer_required` responde con token correcto:

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer change_me" \
  -d '{"message":"hola"}'
```

Comprobar evals protegidas:

```bash
curl http://127.0.0.1:8000/api/evals/telegram?limit=5 \
  -H "Authorization: Bearer change_me"
```

## Documentación ampliada

- `docs/repo_analyzer_telegram.md`
- `docs/telemetry_and_evals_current_state.md`
