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
TELEGRAM_BOT_TOKEN=...
TELEGRAM_ALLOWED_USER_IDS=123456789
```

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

LOCALES puede ejecutarse en modo distribuido dentro de la LAN: Linux mantiene el corpus RAG y Ollama, mientras Windows puede ejecutar FastAPI y consumir evidencias por HTTP.

Guía operativa completa:

- `docs/distributed_rag_lan.md`

## Uso rápido

Arranque local del backend y del bot:

```bash
cd ~/LOCALES
source .venv/bin/activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

```bash
cd ~/LOCALES
source .venv/bin/activate
python scripts/run_telegram.py
```

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
