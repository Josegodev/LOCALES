# LOCALES

## Propósito

`LOCALES` integra un bot local de Telegram con trazabilidad operativa, flujo de chat con LLM y una capa experimental de análisis de repositorio mediante `/repo`.

El objetivo práctico actual es:

- operar el bot de Telegram
- mantener trazas y observabilidad de las interacciones
- responder preguntas sobre un repositorio fijo con herramientas deterministas
- usar fallback LLM solo cuando la pregunta de repositorio es abierta

## Estado actual

- Bot Telegram operativo.
- `/repo` experimental para analizar únicamente `REPO_ANALYZER_PATH`.
- Herramientas deterministas para lectura y búsqueda en repositorio.
- Fallback LLM con Ollama para preguntas abiertas de repositorio.
- Trazas ampliadas para el flujo Telegram.

## Componentes principales

| Componente | Ruta | Función |
| --- | --- | --- |
| Bot Telegram | `app/services/bot_service.py` | Orquesta mensajes Telegram, comandos y persistencia de trazas |
| Servicio `/repo` | `app/services/repo_analyzer_service.py` | Valida configuración de `/repo`, ejecuta routing y formatea respuestas |
| Tools deterministas | `app/services/repo_tools.py` | Resuelve lectura de líneas, búsqueda, árbol y localización de archivos |
| Trazas Telegram | `app/observability/telegram_trace.py` | Persiste `trace_id`, metadata y artefactos de ejecución Telegram |
| Guía `/repo` | `docs/repo_analyzer_telegram.md` | Documentación completa del flujo `/repo` |

## Configuración mínima

Variables necesarias para `/repo`:

```env
REPO_ANALYZER_ENABLED=true
REPO_ANALYZER_PATH=/home/jose-gonzalez-oliva/LOCALES
REPO_ANALYZER_MODEL=granite4.1:8b
REPO_ANALYZER_TEMPERATURE=0.2
```

Variables mínimas del bot Telegram:

```env
TELEGRAM_ENABLED=true
TELEGRAM_BOT_TOKEN=...
TELEGRAM_DEFAULT_MODEL=granite4.1:8b
TELEGRAM_DEFAULT_TEMPERATURE=0.2
TELEGRAM_DEFAULT_RAG_ENABLED=true
TELEGRAM_ALLOWED_USER_IDS=123456789
```

## Recommended runtime: Linux all-in-one

La ruta operativa recomendada ahora es ejecutar todo el runtime principal en Linux:

- bot de Telegram en Linux
- FastAPI en Linux
- RAG local en Linux usando `documents.sqlite`
- Ollama en Linux

Windows puede quedarse como máquina de desarrollo o cliente de prueba. Por ejemplo, puede consultar:

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

Arranque recomendado en Linux con Telegram embebido opcional:

```bash
cd /home/jose-gonzalez-oliva/LOCALES
source .venv/bin/activate

export BACKEND_URL=http://127.0.0.1:8000
export OLLAMA_BASE_URL=http://127.0.0.1:11434
export USE_REMOTE_RAG=false
export DOCUMENTS_DB_PATH=/home/jose-gonzalez-oliva/LOCALES/DB/chunks/documents.sqlite

export TELEGRAM_ENABLED=true
export TELEGRAM_BOT_TOKEN="<NO_COMMIT_REAL_TOKEN>"
export TELEGRAM_DEFAULT_MODEL="granite4.1:8b"
export TELEGRAM_DEFAULT_TEMPERATURE="0.2"
export TELEGRAM_DEFAULT_RAG_ENABLED=true

uvicorn app.main:app --host 0.0.0.0 --port 8000
```

No uses `--reload` ni varios workers con Telegram embebido: ambos pueden duplicar el polling contra Telegram. `scripts/run_telegram.py` se mantiene como runner standalone legacy/opcional.

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

La URL real del backend se introduce en el input `Backend base URL`. La consola prueba `/health`, `/chat` y los endpoints `/telegram/*`, muestra campos de RAG/observabilidad y documenta la arquitectura LOCALES / NUCLEO. Mas detalle en `docs/frontend_console.md` y `docs/telegram_embedded_fastapi.md`.

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

## Documentación ampliada

- `docs/repo_analyzer_telegram.md`
- `docs/telemetry_and_evals_current_state.md`
