# Flujo de ejecución de `POST /chat`

## Punto de entrada real

- Endpoint HTTP: `POST /chat`
- Router: `app/api/routes_chat.py`
- Runtime final: `app/chat_runtime.py::run_chat_request(...)`

## Entrada esperada

La entrada pública se valida con `ChatRequest`:

- `message`: obligatorio, `1..4000` caracteres
- `provider`: opcional, por defecto `ollama`
- `model`: opcional a nivel de schema, pero obligatorio a nivel de contrato runtime
- `max_tokens`: `1..2048`
- `temperature`: `0.0..1.5`
- `top_p`: `0.0..1.0`
- `use_rag`: `true` por defecto
- `top_k`: `1..10`
- `trace_id`: UUID en formato con o sin guiones
- `allowed_source_filenames`
- `active_document_id`
- `active_document_title`
- `active_corpus`
- `last_source_intent`

## Validaciones

### Validaciones de schema

Se hacen antes de entrar en el runtime:

- payload JSON válido;
- presencia de `message`;
- tipos correctos;
- rangos de `temperature`, `top_p`, `top_k`, `max_tokens`;
- saneado de `allowed_source_filenames` a basename.

### Validaciones operativas en runtime

Se hacen dentro de `run_chat_request(...)`:

- `model` explícito es obligatorio;
- `provider/model` deben ser compatibles;
- si `CHAT_AUTH_MODE=disabled`, `/chat` devuelve `403`;
- si `CHAT_AUTH_MODE=bearer_required`, se exige `Authorization: Bearer`.

## Flujo real paso a paso

1. Se resuelven dependencias explícitas o por defecto.
2. Se genera `trace_id` si no viene en el request.
3. Se inicializa contexto de ejecución y se registra un log de entrada.
4. Se valida que exista `model`.
5. Se normaliza el par `provider/model`.
6. Se detecta si el mensaje es un comando como `/creardoc`.
7. Si es `/creardoc`:
   - se desactiva RAG;
   - se llama al LLM para generar Markdown;
   - se invoca `create_document_tool`;
   - se escribe un archivo en `outputs/documents/`;
   - se devuelve respuesta de tool.
8. Si no es comando:
   - se evalúa si conviene usar contexto activo de documento;
   - si `use_rag=true`, se ejecuta retrieval local o remoto;
   - si `use_rag=false`, el `retrieval_status` pasa a `DISABLED`.
9. Si retrieval concluye que no hay evidencia suficiente:
   - se construye safe refusal;
   - no se llama al modelo para una respuesta libre.
10. Si sí hay que generar respuesta:
   - se toma `context["prompt"]`;
   - se llama al proveedor LLM;
   - se miden latencias y métricas disponibles;
   - se normaliza respuesta y se limpia evidencia si corresponde.
11. Se decide `answer_mode`:
   - `documentary_answer`
   - `safe_refusal`
   - `standard_answer`
12. En `finally`, se persiste el run si `persist_trace=true`.
13. También se emite un log final `completed` o `failed`.

## Selección de proveedor y modelo

`app/llm_client.py` hace esta resolución:

- si no hay `provider`, usa `ollama`;
- si `provider=ollama`, intenta resolver el modelo entre los modelos locales disponibles;
- si `provider=openai`, valida el modelo contra una lista soportada;
- si el par es incoherente, devuelve error explícito.

## Uso o no uso de RAG

### Con RAG local

Se usa `DB/chunks/document_context.py::build_document_prompt(...)` cuando:

- `use_rag=true`
- `settings.use_remote_rag=false`

### Con RAG remoto

Se usa `app/rag_client.py::query_remote_rag(...)` cuando:

- `use_rag=true`
- `settings.use_remote_rag=true`

### Sin RAG

Se desactiva cuando:

- `use_rag=false`
- o el flujo entra por `/creardoc`

## Construcción de prompt

### Sin RAG

El mensaje al LLM es el `message` original del usuario.

### Con RAG

El retrieval devuelve un `prompt` enriquecido en `context["prompt"]` que ya incorpora:

- pregunta original;
- chunks recuperados;
- metadatos de intención/corpus;
- filtros por fuentes si aplican.

## Llamada al modelo

El runtime llama a `ask_chat(...)` con:

- `message`
- `provider`
- `model`
- `max_tokens`
- `temperature`
- `top_p`
- `use_rag`

### Qué proveedor aporta qué métricas

- `Ollama`: puede devolver `prompt_eval_count`, `eval_count`, `prompt_eval_duration`, `eval_duration`, `total_duration`, `load_duration`.
- `OpenAI`: en el adaptador inspeccionado devuelve sobre todo `latency_ms`, `temperature_ignored` y texto; no expone ahí métricas nativas equivalentes.

## Extracción de métricas

El runtime intenta persistir:

- `latency_ms`
- `generation_latency_ms`
- `retrieval_latency_ms`
- `tool_latency_ms`
- `tokens_input`
- `tokens_output`
- `tokens_total`
- `prompt_eval_count`
- `eval_count`
- `prompt_eval_duration`
- `eval_duration`
- `total_duration`
- `load_duration`

Si `tokens_total` no viene explícito, se deriva como suma de entrada y salida cuando es posible.

## Construcción de respuesta

La respuesta final es `ChatResponse` y puede incluir:

- estado y metadatos del modelo;
- `retrieval_status`;
- `answer_mode`;
- campos de evidencia;
- warnings públicos;
- métricas;
- metadatos de tool si fue `/creardoc`.

## Persistencia y evaluación

### Persistencia operativa

En `finally`, el runtime intenta guardar el run en `CHAT_RUNS/` mediante `app/observability/chat_runs.py`.

### Evaluación

Los runs guardados se vuelven a cargar desde:

- `app/evals/loader.py`
- `app/chat_runs/store.py`

para construir:

- listados;
- series temporales;
- estadísticas operativas por modelo;
- ejecuciones de eval.

## Superficie de fallo

| Fallo | Comportamiento observado |
| --- | --- |
| Payload inválido | `422` por validación FastAPI/Pydantic. |
| `model` ausente | `400`, código `model_required`. |
| Par `provider/model` inválido | `400`, error explícito. |
| Ollama no disponible | `503`, error de proveedor. |
| OpenAI sin API key | `401`, error de autenticación. |
| Timeout proveedor | `504`. |
| Rate limit OpenAI | `429`. |
| Modelo no disponible | `404`. |
| RAG remoto caído | degradación a `NO_EVIDENCE_FOR_ANSWER` en el cliente RAG. |
| RAG local sin evidencia | safe refusal sin generación libre. |
| Respuesta RAG del modelo solo con marcador `NO_EVIDENCE_FOR_ANSWER` | se fuerza safe refusal y se limpia evidencia. |
| Persistencia de run fallida | el chat puede responder, pero se registra `chat_trace_persist_failed`. |
| CORS no permitido | preflight `400` y log de rechazo. |
| Auth deshabilitada | `/chat` responde `403`. |

## Observaciones de hardening

- El runtime ya evita una respuesta libre cuando no hay evidencia documental suficiente.
- El orden de persistencia en `finally` reduce pérdidas de trazabilidad.
- La principal fragilidad sigue siendo la concentración de lógica en un único módulo.

## Relacionado

- [[ARCHITECTURE]]
- [[RAG_AND_EVIDENCE]]
- [[OBSERVABILITY]]
- [[TECH_DEBT_AND_RISKS]]
- [[GLOSSARY]]
