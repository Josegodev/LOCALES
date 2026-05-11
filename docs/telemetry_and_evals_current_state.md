# Telemetry and Evals Current State

## 1. Scope

Este documento describe el estado actual, verificado en codigo y artefactos del repositorio, de:

- telemetria operacional del flujo principal `Telegram -> /chat -> RAG -> LLM`
- trazabilidad persistida en `logs/telegram_runs/` y en algunos artefactos de `evals/runs/`
- evals de calidad existentes en `scripts/run_chat_evals.py` y `evals/run_telegram_evals.py`
- mecanismos manuales de inspeccion relacionados con RAG y modelos

Este documento no cubre como si ya existiera:

- OpenTelemetry
- spans formales
- collector
- dashboard
- Prometheus
- Grafana
- visualizacion de trazas

Tambien distingue entre el flujo principal en `app/` y un prototipo separado en `llm_lab/`. `llm_lab/` existe en el repositorio, pero no forma parte del pipeline principal `scripts/run_telegram.py -> app/main.py -> app/services/bot_service.py`.

## 2. Executive Summary

El repositorio si tiene telemetria operacional real, pero es heterogenea y esta repartida en varias capas:

- logs estructurados JSON por stdout mediante `app/observability/logging.py`
- trazas persistidas por mensaje Telegram en `logs/telegram_runs/telegram_chat_<YYYYMMDD>.jsonl`
- espejos JSON de algunas ejecuciones Telegram en `evals/runs/chat_eval_<timestamp>_<model>.json`
- metadatos de retrieval y de generacion añadidos en el flujo `/chat`

El repositorio tambien tiene dos sistemas de evals de calidad ya implementados:

- `scripts/run_chat_evals.py` para evals deterministas del endpoint `/chat`
- `evals/run_telegram_evals.py` para barridos por temperatura con salidas `runs.jsonl`, `summary.json` y `summary.md`

Queda fuera del estado actual:

- observabilidad distribuida estandar
- contrato formal de span
- dashboards
- scoring semantico profundo con judge, embeddings o modelo evaluador en el flujo principal

Riesgos operativos observados:

- mezcla de artefactos operacionales y de eval en `evals/runs/`
- contrato de metricas no totalmente uniforme entre traces Telegram, respuesta `/chat` y summaries
- metricas de tokens y duraciones dependen del provider; con OpenAI quedan nulas en el contrato actual
- coexistencia de claves legacy planas y bloque `ollama` duplicado en traces Telegram

## 3. Operational Telemetry

### 3.1 Where telemetry is generated

La telemetria operacional actual se genera en cuatro puntos principales:

1. `app/observability/logging.py`
- expone `log_event(...)`
- emite logs JSON estructurados a stdout
- no persiste por si mismo a fichero

2. `app/services/bot_service.py`
- registra eventos de recepcion, error y completado del flujo Telegram
- al final de cada mensaje llama a `append_telegram_trace(...)`
- tambien llama a `write_telegram_eval_run(...)`

3. `app/main.py`
- registra el ciclo del endpoint `/chat` con `log_event(...)`
- añade `retrieval_status`, `chunk_ids` y `source_filenames` al `ChatResponse`

4. `scripts/run_telegram.py`
- registra telemetria del polling de Telegram
- registra arranque, parada, backoff y errores de red

Adicionalmente existen mecanismos manuales, pero no persistentes:

- `DB/chunks/run_document_rag.py` imprime `retrieval_status`, `chunks` y `scores` por consola
- `scripts/probe_openai_models.py` imprime `model`, `status`, `error_type` y `latency_ms` por consola

### 3.2 Where telemetry is stored

- `logs/telegram_runs/telegram_chat_<YYYYMMDD>.jsonl`
  - persistencia principal por mensaje Telegram
  - un JSON por linea
- `evals/runs/chat_eval_<timestamp>_<model>.json`
  - espejo JSON de una ejecucion Telegram individual
  - se escribe desde `app/observability/telegram_trace.py`
- stdout del proceso
  - eventos `log_event(...)`
  - requiere captura externa si se quiere conservar

`README.md` y `.gitignore` confirman que `logs/telegram_runs/` y `evals/runs/` son artefactos locales no versionados.

### 3.3 Format used

- logs de eventos: JSON estructurado por stdout
- traces Telegram: JSONL
- espejos de trace para eval: JSON identado

Hay un detalle importante: `app/observability/telegram_trace.py` conserva campos planos legacy y, ademas, agrega un bloque `ollama` con algunas de las mismas metricas. El propio archivo contiene un `TODO` indicando que esos campos legacy deberian retirarse mas adelante cuando los lectores consuman el bloque anidado de forma estable.

### 3.4 Available fields

La siguiente tabla resume los campos pedidos para la auditoria. La columna `Required/Optional` se refiere al payload persistido de traces Telegram, no a que siempre tenga valor util.

| Field | Meaning | Source file | Required/Optional | Notes |
| --- | --- | --- | --- | --- |
| `trace_id` | Identificador de traza por mensaje o request | `app/observability/trace.py`, `app/observability/telegram_trace.py`, `app/main.py` | Required | Se genera con UUID hex. |
| `latency_ms` | Latencia total observada | `app/main.py`, `app/adapters/openai_client.py`, `app/observability/telegram_trace.py`, `scripts/run_chat_evals.py`, `evals/run_telegram_evals.py` | Required | En `/chat` y traces Telegram siempre aparece; puede ser `0` en no-evidence o error temprano. |
| `total_duration` | Duracion total devuelta por Ollama | `app/adapters/ollama_client.py`, `app/schemas.py`, `scripts/run_chat_evals.py`, `evals/run_telegram_evals.py` | Optional | En la practica son nanosegundos aunque el nombre no lleve sufijo `_ns`. |
| `eval_duration` | Duracion de generacion devuelta por Ollama | `app/adapters/ollama_client.py`, `app/schemas.py`, `scripts/run_chat_evals.py`, `evals/run_telegram_evals.py` | Optional | Solo se rellena si el provider devuelve esta metrica. |
| `prompt_eval_duration` | Duracion de evaluacion del prompt | `app/adapters/ollama_client.py`, `app/schemas.py`, `scripts/run_chat_evals.py`, `evals/run_telegram_evals.py` | Optional | Solo se rellena en el camino Ollama. |
| `load_duration` | Tiempo de carga del modelo | `app/adapters/ollama_client.py`, `app/schemas.py`, `scripts/run_chat_evals.py`, `evals/run_telegram_evals.py` | Optional | Solo se rellena en el camino Ollama. |
| `tokens_input` | Alias operativo de tokens de entrada | `app/services/bot_service.py`, `app/observability/telegram_trace.py`, `logs/telegram_runs/*.jsonl` | Optional | Se deriva de `prompt_eval_count` en traces Telegram. No se expone en `ChatResponse`. |
| `tokens_output` | Alias operativo de tokens de salida | `app/services/bot_service.py`, `app/observability/telegram_trace.py`, `logs/telegram_runs/*.jsonl` | Optional | Se deriva de `eval_count` en traces Telegram. No se expone en `ChatResponse`. |
| `tokens_total` | Suma de entrada y salida | `app/services/bot_service.py`, `app/observability/telegram_trace.py`, `logs/telegram_runs/*.jsonl` | Optional | Se calcula en traces Telegram si existen ambos conteos. |
| `prompt_eval_count` | Conteo de tokens de entrada segun Ollama | `app/adapters/ollama_client.py`, `app/schemas.py`, `scripts/run_chat_evals.py`, `evals/run_telegram_evals.py` | Optional | En OpenAI queda nulo. |
| `eval_count` | Conteo de tokens de salida segun Ollama | `app/adapters/ollama_client.py`, `app/schemas.py`, `scripts/run_chat_evals.py`, `evals/run_telegram_evals.py` | Optional | En OpenAI queda nulo. |
| `output_tokens_per_second` | Tasa de tokens de salida por segundo | `app/services/bot_service.py`, `app/observability/telegram_trace.py`, `scripts/run_chat_evals.py`, `evals/runs/summarize_telegram_runs.py` | Optional | En Telegram se calcula; en chat evals se deriva de duracion y tokens. |
| `model` | Modelo efectivo usado | `app/main.py`, `app/adapters/ollama_client.py`, `app/adapters/openai_client.py`, `app/observability/telegram_trace.py` | Required | Puede ser `null` en algunos errores. |
| `temperature` | Temperatura solicitada o efectiva | `app/main.py`, `app/adapters/ollama_client.py`, `app/adapters/openai_client.py`, `app/observability/telegram_trace.py` | Optional | En OpenAI puede marcarse `temperature_ignored=true`. |
| `generation_config` | Configuracion de generacion adicional | `app/services/bot_service.py`, `app/observability/telegram_trace.py` | Optional | Campo soportado por la traza, pero no se encontro productor estable en el flujo principal actual. |
| `retrieval_status` | Estado de retrieval RAG | `DB/chunks/document_context.py`, `app/main.py`, `app/observability/telegram_trace.py`, `evals/run_telegram_evals.py` | Optional | Valores observados: `EVIDENCE_FOUND`, `NO_EVIDENCE`, `DISABLED`, `unknown`. |
| `chunk_ids` | Identificadores de chunks usados | `app/main.py`, `app/services/bot_service.py`, `app/observability/telegram_trace.py`, `evals/run_telegram_evals.py` | Optional | En traces Telegram suele estar presente como lista, incluso vacia en error. |
| `source` | Origen del registro | `app/observability/telegram_trace.py`, `evals/run_telegram_evals.py` | Required | Observados `telegram` y `telegram_eval`. |
| `status` | Estado operativo o del payload | `app/main.py`, `DB/chunks/api.py`, `app/observability/telegram_trace.py`, `scripts/run_chat_evals.py`, `evals/run_telegram_evals.py` | Required | En distintos contextos significa exito, error o no-evidence. |
| `error_code` | Codigo de error estructurado | `app/main.py`, `app/services/bot_service.py`, `app/observability/telegram_trace.py`, `scripts/run_chat_evals.py`, `evals/run_telegram_evals.py` | Optional | Se persiste en error; nulo en exito. |
| `error_message` | Mensaje de error | `app/services/bot_service.py`, `app/observability/telegram_trace.py`, `scripts/run_chat_evals.py`, `evals/run_telegram_evals.py` | Optional | No forma parte de `ChatResponse` de exito. |
| `warnings` | Advertencias de metricas o sanitizacion | `app/services/bot_service.py`, `app/observability/telegram_trace.py`, `scripts/run_chat_evals.py`, `evals/run_telegram_evals.py` | Optional | En el flujo principal `/chat` no se encontro productor estable de `warnings`; en chat evals si se generan. |
| `tool_called` | Nombre de tool invocada | no encontrado | no encontrado | No se encontro en `app/`, `scripts/`, `evals/`, `DB/chunks/`, `logs/telegram_runs/` ni `runtime_lab/`. |
| `fallback_used` | Uso de fallback validado | `llm_lab/api.py`, `llm_lab/eval/eval_cases.json` | fuera del flujo principal | No se encontro en el pipeline principal `app/` + `evals/`; solo en `llm_lab/`. |

### 3.5 Optional fields and current limitations

- `generation_config` existe como campo soportado por la traza, pero no se encontro productor estable en el flujo principal auditado.
- `warnings` existe en traces y evals, pero su uso es mucho mas claro en `scripts/run_chat_evals.py` que en `/chat`.
- `tokens_input`, `tokens_output` y `tokens_total` existen en traces Telegram, pero no en la respuesta `/chat`; por eso algunos summaries de eval muestran medias nulas para esos campos.
- `source_filenames` esta soportado y se persiste, pero en artefactos reales se observan registros antiguos con listas vacias y registros mas recientes con filenames poblados.

### 3.6 Related commands and scripts

- `scripts/run_telegram.py`
  - polling de Telegram y envio de mensajes
  - genera logs estructurados y dispara la persistencia de traces
- `DB/chunks/run_document_rag.py`
  - utilidad manual para inspeccionar retrieval local
  - imprime `retrieval_status`, `chunks` y `scores`
- `scripts/probe_openai_models.py`
  - sonda manual de modelos OpenAI soportados
  - imprime `model`, `status`, `error_type` y `latency_ms`

## 4. Evaluation System

### 4.1 Current eval families

Hay dos familias principales de evals de calidad en el sistema actual:

1. Chat evals deterministas
- archivo principal: `scripts/run_chat_evals.py`
- objetivo: validar el endpoint `/chat` con reglas deterministas
- casos: `evals/cases/chat_cases.json`
- baseline opcional: `evals/baselines/chat_baseline.json`

2. Telegram-style eval runs por temperatura
- archivo principal: `evals/run_telegram_evals.py`
- objetivo: repetir un caso o conjunto de casos contra `/chat` con varias temperaturas
- salida: carpeta por run en `evals/runs/telegram_eval_<model>_<timestamp>/`

Tambien existe un prototipo separado:

3. `llm_lab`
- tiene `llm_lab/eval/eval_cases.json`
- usa `fallback_used`
- no forma parte del flujo principal `app/`

### 4.2 Cases, outputs and captured metrics

`scripts/run_chat_evals.py`:

- carga casos desde `evals/cases/chat_cases.json`
- genera `trace_id` determinista por caso
- llama a `POST /chat`
- evalua:
  - HTTP
  - respuesta no vacia
  - terminos esperados
  - terminos prohibidos
  - longitud
  - validez de metricas
- guarda un JSON agregado en `evals/runs/chat_eval_<run_id>.json`
- opcionalmente compara contra baseline y detecta drift

`evals/run_telegram_evals.py`:

- pide configuracion interactiva
- construye payloads con `model`, `temperature`, `use_rag`, `top_k` y `allowed_source_filenames`
- llama repetidamente a `POST /chat`
- sanea payloads pesados de RAG
- escribe:
  - `runs.jsonl`
  - `summary.json`
  - `summary.md`
- calcula por temperatura:
  - `pass_rate`
  - `avg_drift_score`
  - `avg_latency_ms`
  - conteos de `retrieval_status`
  - conteos de `status`
  - fallos de source match

### 4.3 Eval components

| Component | Path | Purpose | Output |
| --- | --- | --- | --- |
| Chat cases | `evals/cases/chat_cases.json` | Casos deterministas para `/chat` | Lista JSON de casos |
| Chat eval runner | `scripts/run_chat_evals.py` | Ejecutar casos contra `/chat` y validar contrato | `evals/runs/chat_eval_<run_id>.json` |
| Chat baseline | `evals/baselines/chat_baseline.json` | Referencia para comparar drift entre runs | JSON baseline |
| Telegram eval runner | `evals/run_telegram_evals.py` | Ejecutar barridos por temperatura con RAG | Carpeta `evals/runs/telegram_eval_<model>_<timestamp>/` |
| Telegram eval records | `evals/runs/telegram_eval_mistral_20260509T155437394885Z/runs.jsonl` | Ejemplo real de registros por repeticion | JSONL |
| Telegram eval summary | `evals/runs/telegram_eval_mistral_20260509T155437394885Z/summary.json` | Resumen agregado por temperatura | JSON |
| Telegram eval markdown | `evals/runs/telegram_eval_mistral_20260509T155437394885Z/summary.md` | Resumen legible para humanos | Markdown |
| Telegram run summarizer | `evals/runs/summarize_telegram_runs.py` | Agrupar runs `chat_eval_*.json` por modelo y temperatura | Salida por consola |
| Eval overview | `evals/README.md` | Explicar objetivos y limites del metodo | Documentacion |

### 4.4 Metrics currently captured by evals

En `scripts/run_chat_evals.py` se capturan o derivan:

- `latency_ms`
- `client_latency_ms`
- `error_code`
- `error_message`
- `warnings`
- `prompt_eval_count`
- `eval_count`
- `prompt_eval_duration`
- `eval_duration`
- `total_duration`
- `load_duration`
- `tokens_input`
- `tokens_output`
- `tokens_total`
- `output_tokens_per_second`
- `prompt_tokens_per_second`
- agregados totales y comparacion contra baseline

En `evals/run_telegram_evals.py` se capturan o derivan:

- `status`
- `http_status`
- `latency_ms`
- `retrieval_status`
- `chunk_ids`
- `source_filenames`
- `rag_payload_sanitized`
- `sanitized_fields`
- `eval_result.pass`
- `eval_result.drift_score`
- `forbidden_terms_found`
- `missing_expected_terms`

### 4.5 Current limitations of the eval system

- `eval_cases.json` con ese nombre exacto no se encontro en `evals/`; el archivo principal real es `evals/cases/chat_cases.json`.
- `summarize_telegram_runs.py` no esta en `scripts/`; el archivo real es `evals/runs/summarize_telegram_runs.py`.
- `evals/run_telegram_evals.py` espera promediar `tokens_input`, `tokens_output` y `tokens_total`, pero el ejemplo real `runs.jsonl` contiene `prompt_eval_count` y `eval_count`, no esos aliases. El resultado visible es `avg_tokens_*: null` en `summary.json`.
- El sistema si detecta drift, pero lo hace con reglas deterministas y comparaciones estructurales; no se encontro judge semantico ni scoring por embeddings en el flujo principal.

## 5. Difference Between Telemetry and Evals

La diferencia actual en este repo es clara:

- telemetria operacional = que paso en una ejecucion real
- evals = si la respuesta o el comportamiento cumplieron un criterio de calidad definido

Ejemplos operacionales del repo:

- `logs/telegram_runs/telegram_chat_20260509.jsonl`
  - guarda por mensaje `trace_id`, `model`, `latency_ms`, `retrieval_status`, `chunk_ids` y errores
- `app/main.py`
  - emite `fastapi.chat.completed` o `fastapi.chat.failed`
- `scripts/run_telegram.py`
  - emite eventos de polling y backoff

Ejemplos de eval del repo:

- `scripts/run_chat_evals.py`
  - decide si un caso `passed` o no
  - compara contra baseline
- `evals/run_telegram_evals.py`
  - calcula `drift_score`, `pass_rate` y fallos de source matching

Ejemplo concreto:

- un registro de `logs/telegram_runs/telegram_chat_20260509.jsonl` puede decir que una llamada tuvo `status=ok`, `latency_ms=2876` y `retrieval_status=EVIDENCE_FOUND`
- pero `evals/runs/telegram_eval_mistral_20260509T155437394885Z/summary.json` puede decir que el `pass_rate` fue `0.0` porque la respuesta incluyo terminos prohibidos

Eso significa:

- operacionalmente, la llamada funciono
- en calidad, la respuesta fallo el criterio definido

## 6. Current Data Flow

### 6.1 Main Telegram production-like flow

`Telegram update`
-> `scripts/run_telegram.py`
-> `app/services/bot_service.py`
-> `POST /chat` en `app/main.py`
-> `DB/chunks/document_context.py` para retrieval
-> `app/llm_client.py`
-> `app/adapters/ollama_client.py` o `app/adapters/openai_client.py`
-> respuesta a Telegram
-> `logs/telegram_runs/telegram_chat_<YYYYMMDD>.jsonl`
-> `evals/runs/chat_eval_<timestamp>_<model>.json` (espejo por mensaje)

### 6.2 Deterministic chat eval flow

`scripts/run_chat_evals.py`
-> `POST /chat`
-> valida respuesta y metricas
-> `evals/runs/chat_eval_<run_id>.json`
-> opcional comparacion con `evals/baselines/chat_baseline.json`

### 6.3 Telegram eval sweep flow

`evals/run_telegram_evals.py`
-> `POST /chat`
-> sanitizacion de payload RAG
-> `evals/runs/telegram_eval_<model>_<timestamp>/runs.jsonl`
-> `evals/runs/telegram_eval_<model>_<timestamp>/summary.json`
-> `evals/runs/telegram_eval_<model>_<timestamp>/summary.md`

### 6.4 Standalone RAG helper flow

`DB/chunks/run_document_rag.py`
-> `DB/chunks/document_context.py`
-> `DB/chunks/lmstudio_client.py`
-> salida por consola

Este ultimo flujo muestra estado de retrieval, pero no escribe trazas persistentes en el sistema principal.

## 7. Known Gaps

Huecos confirmados en el repo actual:

- no hay OpenTelemetry
- no hay spans formales
- no hay collector
- no hay dashboard
- no hay Prometheus
- no hay Grafana
- no hay trazabilidad visual
- no hay contrato formal de span

Huecos o inconsistencias operativas confirmadas:

- `evals/runs/` mezcla artefactos de distinta naturaleza: espejos de ejecucion real, runs de eval determinista y carpetas de eval por temperatura
- las metricas de tokens y duraciones no son uniformes entre traces Telegram y resultados de eval
- OpenAI no rellena `prompt_eval_count`, `eval_count`, `prompt_eval_duration`, `eval_duration`, `total_duration` ni `load_duration` en el contrato actual
- `tool_called` no encontrado
- `fallback_used` no encontrado en el flujo principal; solo existe en `llm_lab/`
- `runtime_lab/` no encontrado

Huecos que no aplican tal cual:

- `drift detection` no es un hueco total, porque si existe en dos formas:
  - comparacion contra baseline en `scripts/run_chat_evals.py`
  - `drift_score` en `evals/run_telegram_evals.py`

## 8. Recommended Next Step

El siguiente paso minimo y no invasivo recomendado no es implementar OpenTelemetry todavia, sino normalizar logicamente los JSON/JSONL actuales para que ya se comporten como spans logicos.

Paso recomendado:

- definir una convencion documental de etapas para los registros actuales
- no cambiar providers ni introducir dependencias nuevas
- empezar por nombrar etapas y aclarar que campos pertenecen a cada una

Nombres de spans logicos que encajan con el estado actual:

- `telegram.receive`
- `api.chat`
- `rag.retrieve`
- `prompt.build`
- `llm.generate`
- `response.validate`
- `telegram.send`

Aplicado al estado actual, esto serviria para:

- mapear `trace_id` a una unica conversacion tecnica por request
- separar latencia total de latencias parciales
- reducir la ambiguedad entre trace operacional y eval de calidad
- preparar una futura migracion incremental a OpenTelemetry sin reescribir el sistema

## 9. Files Inspected

- `README.md` - describe arquitectura general, trazabilidad por `request_id` y limites actuales.
- `.gitignore` - confirma que `logs/`, `logs/telegram_runs/`, `evals/runs/` y `*.jsonl` son artefactos locales.
- `app/observability/logging.py` - logger JSON estructurado a stdout.
- `app/observability/trace.py` - generacion de `trace_id`.
- `app/observability/telegram_trace.py` - persistencia de traces Telegram y espejo JSON para eval.
- `app/observability/__init__.py` - exporta API de observabilidad usada por el resto del sistema.
- `app/services/bot_service.py` - une Telegram, `/chat`, persistencia de trace y espejo de eval.
- `app/main.py` - endpoint `/chat`, integracion RAG, log_event y payload de respuesta.
- `app/schemas.py` - contrato `ChatRequest` y `ChatResponse`.
- `app/llm_client.py` - seleccion de provider/modelo para chat.
- `app/adapters/ollama_client.py` - metricas detalladas de Ollama.
- `app/adapters/openai_client.py` - respuesta OpenAI con `latency_ms` y `temperature_ignored`.
- `app/rag_store.py` - wrapper de compatibilidad para retrieval y campo `source`.
- `scripts/run_telegram.py` - polling de Telegram y logs operacionales.
- `scripts/run_chat_evals.py` - eval runner determinista contra `/chat`.
- `scripts/probe_openai_models.py` - probe manual de modelos OpenAI.
- `evals/README.md` - documenta objetivos y limites del sistema de chat evals.
- `evals/cases/chat_cases.json` - casos deterministas para `/chat`.
- `evals/baselines/chat_baseline.json` - baseline de referencia.
- `evals/run_telegram_evals.py` - eval runner por temperatura para el flujo Telegram-style.
- `evals/runs/summarize_telegram_runs.py` - resumen por modelo y temperatura de `chat_eval_*.json`.
- `evals/runs/telegram_eval_mistral_20260509T155437394885Z/runs.jsonl` - ejemplo real de registros de eval por repeticion.
- `evals/runs/telegram_eval_mistral_20260509T155437394885Z/summary.json` - ejemplo real de resumen agregado.
- `logs/telegram_runs/telegram_chat_20260509.jsonl` - ejemplo real de telemetria operacional persistida.
- `DB/chunks/document_context.py` - origen de `retrieval_status`, chunks y prompt RAG.
- `DB/chunks/api.py` - API RAG standalone con `status`, `chunks` y `answer`, sin observabilidad principal.
- `DB/chunks/run_document_rag.py` - utilidad CLI de inspeccion de retrieval.
- `runtime_lab/` - no encontrado.
- `llm_lab/api.py` - prototipo separado donde si aparece `fallback_used`.
- `llm_lab/README.md` - confirma que `llm_lab` escribe traces propios en `llm_lab/artifacts`.
- `llm_lab/eval/eval_cases.json` - confirma que `eval_cases.json` existe solo en ese prototipo separado.
