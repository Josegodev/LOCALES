# Telegram /repo analyzer

## Estado

V1 experimental.

Analiza únicamente el repositorio configurado en `REPO_ANALYZER_PATH`. No acepta `repo_path` dinámico desde Telegram.

Este flujo no forma parte de un `PolicyEngine`, `Planner`, `ToolRegistry` o `Runtime` separado. En `LOCALES`, el camino real es el servicio de Telegram actual.

## Propósito

El comando `/repo` permite hacer consultas sobre el repositorio configurado para el bot.

Hay dos modos de respuesta:

- herramientas deterministas para operaciones exactas
- fallback LLM para preguntas abiertas

La idea es simple:

- si pides una línea concreta o una búsqueda textual, no hace falta un LLM
- si pides una explicación o un resumen, se usa el fallback con `RepoChatSession`

## Flujo

```text
Telegram /repo
    ->
app/services/bot_service.py
    ->
app/services/repo_analyzer_service.py
    ->
app/services/repo_tools.py
    ->
deterministic tool / fallback LLM
```

Resumen del flujo:

1. Telegram recibe `/repo <pregunta>`.
2. `bot_service.py` detecta el comando.
3. `repo_analyzer_service.py` valida configuración y enruta la pregunta.
4. `repo_tools.py` intenta resolverla con una herramienta determinista.
5. Si no encaja en una herramienta exacta, usa `ask_repo_llm`.

## Configuración

Variables de entorno necesarias:

```env
REPO_ANALYZER_ENABLED=true
REPO_ANALYZER_PATH=/home/jose-gonzalez-oliva/LOCALES
REPO_ANALYZER_MODEL=granite4.1:8b
REPO_ANALYZER_TEMPERATURE=0.2
```

Significado:

- `REPO_ANALYZER_ENABLED`: habilita o deshabilita `/repo`
- `REPO_ANALYZER_PATH`: ruta fija del repositorio analizado
- `REPO_ANALYZER_MODEL`: modelo para el fallback LLM
- `REPO_ANALYZER_TEMPERATURE`: temperatura para el fallback LLM

## Herramientas disponibles

| Tool | Uso principal | Usa LLM |
| --- | --- | --- |
| `repo_tree` | devolver una estructura resumida del repo | no |
| `find_file` | localizar archivos por nombre o ruta relativa | no |
| `read_file_range` | leer una línea o un rango de líneas | no |
| `search_text` | buscar texto dentro del repo | no |
| `ask_repo_llm` | responder preguntas abiertas | sí |

## Routing actual

| Pregunta | Routing |
| --- | --- |
| `línea 14 de config.py` | `read_file_range` |
| `líneas 10-20 de app/config.py` | `read_file_range` |
| `busca REPO_ANALYZER_ENABLED` | `search_text` |
| `dónde está config.py` | `find_file` |
| `estructura del repo` | `repo_tree` |
| pregunta abierta | `ask_repo_llm` |

## Comandos de Telegram

Ejemplos soportados:

```text
/repo línea 14 de config.py
/repo líneas 10-20 de app/config.py
/repo busca REPO_ANALYZER_ENABLED
/repo dónde está config.py
/repo estructura del repo
/repo Qué riesgos ves en este repo?
```

Comportamiento esperado:

- `/repo línea 14 de config.py`
  - devuelve una línea concreta sin llamar al LLM
- `/repo líneas 10-20 de app/config.py`
  - devuelve un rango de líneas sin llamar al LLM
- `/repo busca REPO_ANALYZER_ENABLED`
  - devuelve coincidencias de texto sin llamar al LLM
- `/repo dónde está config.py`
  - devuelve coincidencias de archivo sin llamar al LLM
- `/repo estructura del repo`
  - devuelve un árbol resumido sin llamar al LLM
- `/repo Qué riesgos ves en este repo?`
  - usa el fallback LLM con `RepoChatSession` y Ollama

## Formato de respuesta

Respuestas típicas:

- `read_file_range`

```text
app/config.py líneas 14-14:
14: repo_analyzer_enabled: bool = False
```

- `find_file`

```text
Coincidencias para config.py:
- app/config.py
```

- `search_text`

```text
Coincidencias para REPO_ANALYZER_ENABLED:
- app/config.py:24: repo_analyzer_enabled: bool = False
```

- `repo_tree`

```text
Estructura del repo (LOCALES):
- app/config.py
- app/services/repo_tools.py
- tests/test_repo_command.py
```

- error

```text
Error repo_analyzer:
FILE_NOT_FOUND - No se encontró el archivo: config.py
```

## Trazabilidad

La traza del flujo `/repo` incluye:

- `trace_id`
- `timestamp`
- `source`
- `command`
- `repo_path`
- `model`
- `temperature`
- `question`
- `repo_tool`
- `requested_file`
- `resolved_path`
- `start_line`
- `end_line`
- `query`
- `evidence_files`
- `status`
- `error_code`
- `error_message`
- `latency_ms`

Esto permite distinguir:

- qué pregunta llegó
- qué herramienta se usó
- si hubo fallback LLM o no
- qué archivo o rango se resolvió

## Límites y restricciones

Este flujo actual:

- no edita archivos
- no ejecuta comandos externos
- no hace `git`
- no instala dependencias
- no acepta `repo_path` desde Telegram
- no hace análisis multi-repo
- no añade memoria conversacional del repositorio

Además, las herramientas deterministas no deben leer:

- `.env`
- `.sqlite`
- `.db`
- PDFs
- imágenes
- binarios
- `.git`
- `.venv`
- cachés

## Riesgos pendientes

- El fallback LLM depende de Ollama.
- El fallback LLM depende del workspace `Analyzer`.
- Las reglas de exclusión están duplicadas localmente en `app/services/repo_tools.py`.
- Si faltan dependencias como `pytest` o `pydantic`, los tests no arrancan en algunos entornos.
- No hay memoria conversacional de repo.
- No hay edición ni aplicación de cambios desde `/repo`.

## Deuda técnica aceptada en V1

La capa determinista vive localmente en `LOCALES`, mientras que el fallback LLM sigue dependiendo de `Analyzer`.

Esa duplicación es intencionada en esta V1 para mantener:

- cambios mínimos
- menor acoplamiento operativo del bot
- herramientas exactas disponibles incluso cuando la parte LLM falle

## Verificación

Comandos de verificación:

```bash
python3 -m compileall app scripts tests
python3 -m pytest -q
```

Pruebas manuales en Telegram:

```text
/repo línea 14 de config.py
/repo busca REPO_ANALYZER_ENABLED
/repo estructura del repo
/repo Qué riesgos ves en este repo?
```
