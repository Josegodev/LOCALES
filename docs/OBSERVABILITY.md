# Observabilidad actual

## Resumen

La observabilidad actual de LOCALES es local, orientada a ficheros y logs JSON. No se detecta un backend de tracing distribuido ni una plataforma externa de métricas. Aun así, el sistema ya conserva señales útiles para debugging y hardening.

## Fuentes observables detectadas

### Logs estructurados

- Implementación: `app/observability/logging.py`
- Formato: JSON en stdout
- Campos base:
  - `component`
  - `event`
  - `trace_id` cuando aplica
  - `request_id` cuando aplica
  - cualquier campo adicional no nulo

### Trace IDs

- Generación: `app/observability/trace.py`
- Formato por defecto: `uuid4().hex`
- Observación:
  - el schema acepta UUID con o sin guiones;
  - el runtime genera por defecto sin guiones.

### Persistencia de chat runs

- Implementación: `app/observability/chat_runs.py`
- Ubicación principal observada: `CHAT_RUNS/`
- Forma: un archivo JSON por run
- Uso posterior:
  - `app/chat_runs/store.py`
  - `app/evals/loader.py`
  - endpoints `/api/chat-runs*` y `/api/runs*`

### Persistencia de chat traces JSONL

- Implementación: `app/observability/chat_trace.py`
- Ubicación por defecto: `data/chat_traces.jsonl`
- Estado observado:
  - existe como capa de trazas;
  - la API inspeccionada de traces usa `list_chat_runs(...)`, no este almacén, así que hay riesgo de drift.

### Persistencia de eval runs

- Ubicación: `evals/runs/`
- Forma: JSON por ejecución de eval
- Uso: baseline y métricas operativas/evaluativas

## Métricas detectadas

### Métricas de runtime

- `latency_ms`
- `generation_latency_ms`
- `retrieval_latency_ms`
- `tool_latency_ms`
- `status`
- `error_code`
- `error_message`
- `error_type`

### Métricas de tokens

- `tokens_input`
- `tokens_output`
- `tokens_total`
- `output_tokens_per_second` derivado en cargadores/estadísticas

### Métricas nativas de proveedor

#### Ollama

Detectadas en `app/adapters/ollama_client.py`:

- `prompt_eval_count`
- `eval_count`
- `prompt_eval_duration`
- `eval_duration`
- `total_duration`
- `load_duration`

#### OpenAI

Detectadas en `app/adapters/openai_client.py`:

- `latency_ms`
- `temperature_ignored`

No se observa en ese adaptador extracción equivalente de métricas nativas de tokens/duración. Por tanto, la observabilidad es más pobre que con Ollama.

## Niveles de observabilidad inferidos

`app/chat_runs/store.py` infiere:

- `provider_native` cuando hay campos nativos como `eval_duration`;
- `runtime_only` cuando solo hay latencias generales.

Esto es útil, pero hoy es inferido, no persistido explícitamente desde el runtime.

## Campos recomendados mínimos

| Campo | Estado observado |
| --- | --- |
| `trace_id` | Sí |
| `timestamp` | Parcial (`created_at` y a veces `timestamp`) |
| `provider` | Sí |
| `model` | Sí |
| `temperature` | Sí |
| `tokens_input` | Parcial |
| `tokens_output` | Parcial |
| `latency_ms` | Sí |
| `retrieval_status` | Sí |
| `chunk_ids` | Sí |
| `source_filenames` | Sí |
| `status` | Sí |
| `error_type` | Parcial |
| `fallback_used` | Sí |

## Qué se puede depurar hoy

- si una petición falló o no;
- qué proveedor/modelo se usó;
- si hubo RAG o no;
- si hubo fallback;
- si hubo evidencia y de qué archivos vino;
- latencia total y parciales principales;
- runs por modelo;
- tasa de error;
- series temporales básicas;
- stats operativas por temperatura/modelo.

## Qué no se observa bien todavía

- trazas por paso interno tipo span;
- coste monetario real por proveedor;
- uso de tokens de OpenAI con la misma riqueza que Ollama;
- distinción persistida y cerrada entre run operativo, trace y eval;
- correlación explícita entre logs JSON y todos los artefactos en disco;
- versionado explícito del contrato de observabilidad más allá de `chat_run.v1`.

## Drift y contradicciones detectadas

### Runs vs traces

- `CHAT_RUNS/` es la fuente viva de listados y métricas.
- `data/chat_traces.jsonl` sigue existiendo.
- La nomenclatura “trace” y “run” no está completamente consolidada.

### Ruta configurada de runs

- `.env.example` usa `CHAT_RUNS_PATH=data/chat_runs.jsonl`.
- El cargador real de runs opera como directorio de JSON por archivo.
- Esto es un riesgo directo de configuración ambigua.

## Recomendaciones mínimas de hardening

1. Persistir explícitamente `observability_level` desde el runtime.
2. Cerrar un único almacén canónico para runs/traces.
3. Unificar `created_at` y `timestamp`.
4. Documentar oficialmente qué campos son obligatorios en un run exitoso y en uno fallido.
5. Añadir un campo explícito para `response_source` o equivalente si en el futuro hay tools o planner.

## Relacionado

- [[RUNTIME_FLOW]]
- [[LOCAL_DEPLOYMENT]]
- [[TECH_DEBT_AND_RISKS]]
- [[GLOSSARY]]
