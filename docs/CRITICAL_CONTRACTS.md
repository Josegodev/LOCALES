# Contratos críticos del runtime

## 1. Resumen

El endpoint `POST /chat` depende de varias fronteras contractuales que tienen que mantenerse coherentes para que el sistema siga siendo trazable y determinista.

Las más críticas son:

- contrato HTTP de entrada en `app/api/routes_chat.py`;
- contrato de datos `ChatRequest` y `ChatResponse` en `app/schemas.py`;
- contrato operativo de ejecución en `app/chat_runtime.py`;
- contrato de resolución `provider/model` en `app/llm_client.py`;
- contrato de inyección en `app/chat/dependencies.py`;
- contratos auxiliares que participan directamente en la ejecución:
  - `app/rag_client.py`
  - `DB/chunks/document_context.py`
  - `app/observability/chat_runs.py`
  - `app/tools/create_document.py`
  - `app/main.py`

Lo importante aquí no es “qué módulos existen”, sino qué límites no conviene romper cuando se toque el runtime:

- que `ChatRequest` siga entrando;
- que `ChatResponse` siga saliendo con los campos esperados;
- que `trace_id`, `retrieval_status`, `chunk_ids` y `source_filenames` no se pierdan;
- que la resolución `provider/model` siga fallando de forma explícita;
- que la persistencia de runs siga registrando lo que la respuesta pública no expone.

## 2. Contrato de entrada `/chat`

### Módulos implicados

- `app/api/routes_chat.py`
- `app/schemas.py`
- `app/chat_runtime.py`
- `app/auth.py`

### Contrato observado

`app/api/routes_chat.py` expone:

- `@router.post("/chat", response_model=ChatResponse)`

La request pública se valida con `ChatRequest` en `app/schemas.py`.

#### Campos del esquema `ChatRequest`

| Campo | Tipo | Obligatorio | Default observado | Validación observada |
| --- | --- | --- | --- | --- |
| `message` | `str` | Sí | Sin default | `min_length=1`, `max_length=4000` |
| `provider` | `str \| None` | No | `None` | Sin validador específico en schema |
| `model` | `str \| None` | No en schema | `None` | Obligatorio más tarde en runtime |
| `max_tokens` | `int \| None` | No | `None` | `ge=1`, `le=2048` |
| `temperature` | `float \| None` | No | `None` | `normalize_temperature`, rango `0.0..1.5` |
| `top_p` | `float \| None` | No | `None` | `normalize_top_p`, rango `0.0..1.0` |
| `use_rag` | `bool \| None` | No | `True` | Sin validador adicional |
| `top_k` | `int \| None` | No | `3` | `ge=1`, `le=10` |
| `trace_id` | `str \| None` | No | `None` | UUID con o sin guiones, longitud `32..36` |
| `user_id` | `int \| None` | No | `None` | Sin validación adicional |
| `chat_id` | `int \| None` | No | `None` | Sin validación adicional |
| `allowed_source_filenames` | `list[str]` | No | `[]` | Se reduce a basename y se deduplica |
| `active_document_id` | `int \| None` | No | `None` | `ge=1` |
| `active_document_title` | `str \| None` | No | `None` | `min_length=1`, `max_length=255` |
| `active_corpus` | `str \| None` | No | `None` | `min_length=1`, `max_length=64` |
| `last_source_intent` | `str \| None` | No | `None` | `min_length=1`, `max_length=64` |

#### Defaults efectivos en runtime

En `app/chat_runtime.py`, además del schema, se aplican estos defaults operativos:

- `trace_id = request.trace_id or new_trace_id()`
- `provider = request.provider or "ollama"`
- `temperature = request.temperature or TEMPERATURE_DEFAULT`
- `effective_max_tokens = request.max_tokens or settings.max_tokens`
- `use_rag = True if request.use_rag is None else bool(request.use_rag)`
- `top_k = request.top_k or 3`

### Errores esperados

#### Antes de entrar al runtime

- `422` si el payload no cumple `ChatRequest`
- `403` si falla `require_chat_access(...)`

#### Dentro del runtime

- `400` con `code="model_required"` si `model` falta o viene vacío
- `400` con `code="invalid_provider_model_pair"` si `provider/model` no son coherentes
- `401` si OpenAI no tiene API key válida
- `404` si el modelo no está disponible
- `429` si OpenAI devuelve rate limit
- `503` si el proveedor no está disponible
- `504` si el proveedor agota timeout
- `500` con `code="chat_internal_error"` en errores no controlados

### Contrato implícito

- Aunque `model` es opcional en `ChatRequest`, el runtime lo trata como obligatorio.
- `provider` no se valida en el schema; la validación real ocurre en `app/llm_client.py`.
- `use_rag=True` es el comportamiento nominal del sistema.

### Riesgo de drift

- `model` opcional en schema pero obligatorio en runtime.
- `ErrorResponse` existe en `app/schemas.py`, pero `routes_chat.py` no lo declara como `response_model` de error.

## 3. Contrato de salida `/chat`

### Módulos implicados

- `app/schemas.py`
- `app/chat_runtime.py`
- `app/chat/fallback.py`
- `app/tools/create_document.py`

### Contrato observado

La respuesta exitosa pública se valida con `ChatResponse`.

#### Campos observados en `ChatResponse`

##### Estado y trazabilidad

- `trace_id`
- `status`
- `answer`
- `latency_ms`
- `warnings`

##### Modelo y proveedor

- `provider`
- `model`
- `temperature`
- `temperature_ignored`
- `use_rag`

##### RAG y evidencia

- `retrieval_status`
- `answer_mode`
- `query_original`
- `query_normalized`
- `query_terms`
- `quoted_terms`
- `source_intent`
- `selected_corpus`
- `active_document_id`
- `active_document_title`
- `active_context_used`
- `active_context_reason`
- `evidence_used`
- `fallback_used`
- `query_expansion_used`
- `query_expansion_reason`
- `expanded_query_terms`
- `candidate_filenames`
- `selected_filenames`
- `chunks`
- `chunk_ids`
- `document_ids`
- `source_filenames`
- `scores`
- `ranking_scores`

##### Métricas públicas

- `prompt_eval_count`
- `eval_count`
- `prompt_eval_duration`
- `eval_duration`
- `total_duration`
- `load_duration`
- `tool_latency_ms`

##### Campos de tool `/creardoc`

- `command`
- `tool_called`
- `tool_result_status`
- `document_path`
- `document_filename`
- `chars_written`
- `overwrite_requested`
- `overwrite_applied`
- `overwrite_reason`

### Respuesta de error observada

La salida de error de `POST /chat` no usa `ChatResponse`.

Usa `HTTPException.detail` con un payload tipo:

- `trace_id`
- `status="error"`
- `code`
- `message`
- `retrieval_status`
- `chunk_ids`
- `document_ids`
- `source_filenames`
- `query_original`
- `use_rag`
- `warnings`

En algunos errores de `/creardoc` también aparecen:

- `command`
- `tool_called`
- `tool_result_status`
- `error_type`

### Contrato implícito

- `ChatResponse` es el contrato de éxito.
- El contrato de error es un diccionario ad hoc dentro de `HTTPException`, no un modelo Pydantic único.
- `warnings` admite mezcla de `str` y `dict`.

### Riesgo de drift

- `tokens_input`, `tokens_output` y `tokens_total` existen en runtime y persistencia, pero no en `ChatResponse`.
- `error_type` existe en persistencia y logging, pero no en `ChatResponse`.
- `generation_latency_ms` y `retrieval_latency_ms` se persisten, pero no se devuelven en la respuesta pública.

## 4. Contrato proveedor/modelo

### Módulos implicados

- `app/llm_client.py`
- `app/adapters/ollama_client.py`
- `app/adapters/openai_client.py`
- `app/chat_runtime.py`

### Contrato observado

La selección se resuelve en `app.llm_client.resolve_provider_model(...)`.

#### Selección de `provider`

- si `provider` es `None`, se usa `"ollama"`
- se normaliza con `strip().lower()`

#### Selección de `model`

- para `ollama`:
  - usa el modelo recibido si es válido;
  - si falta, intenta el configurado por settings;
  - si sigue faltando, intenta el primer modelo disponible vía `list_models()`;
  - si no hay modelos, lanza `llm_model_not_available`
- para `openai`:
  - si falta, usa `DEFAULT_OPENAI_MODEL`
  - después valida contra `SUPPORTED_MODELS`

#### Combinaciones válidas observadas

- `provider="ollama"` con modelo no OpenAI
- `provider="openai"` con modelo soportado por OpenAI

#### Combinaciones inválidas observadas

- `provider="ollama"` con modelo tipo `gpt-*`
- `provider="openai"` con modelo tipo `granite4.1:8b`
- `provider` distinto de `ollama` u `openai`

### Dónde se valida

- validación semántica principal: `app/llm_client.py`
- obligación de `model` explícito: `app/chat_runtime.py`

### Qué pasa si falta `model`

#### Contrato observado

`app/chat_runtime.py` lanza:

- `400`
- `code="model_required"`
- mensaje: `El contrato de /chat requiere un model explicito.`

#### Observación importante

Esto ocurre antes de aprovechar el default de OpenAI o la resolución automática de Ollama.

### Qué pasa si `provider/model` no coinciden

`resolve_provider_model(...)` lanza `LLMClientError` con:

- `code="invalid_provider_model_pair"`

El runtime traduce eso a:

- `HTTP 400`
- `message="No se pudo generar respuesta del modelo."`

### Contrato implícito

- existe una doble capa:
  - `ChatRequest` acepta casi cualquier `provider/model` a nivel estructural;
  - `llm_client` cierra el contrato semántico real.

### Riesgo de drift

- el schema no expresa la obligación de `model`;
- la política real de modelos soportados OpenAI vive en código, no en contrato público versionado;
- Ollama acepta resolución por prefijo único, OpenAI no.

## 5. Contrato RAG

### Módulos implicados

- `app/chat_runtime.py`
- `app/rag_client.py`
- `DB/chunks/document_context.py`
- `rag_service/main.py`

### Cuándo se usa RAG

#### RAG activado

Se usa cuando:

- `use_rag` es verdadero
- no se entra por el comando `/creardoc`

#### RAG desactivado

Se desactiva cuando:

- `use_rag=false`
- o el mensaje es un comando `/creardoc`

En ese caso:

- `retrieval_status="DISABLED"`

### RAG local vs remoto

#### RAG local

Se usa si:

- `settings.use_remote_rag == False`

Y llama a:

- `DB/chunks/document_context.build_document_prompt(...)`

#### RAG remoto

Se usa si:

- `settings.use_remote_rag == True`

Y llama a:

- `app.rag_client.query_remote_rag(...)`

El cliente remoto manda:

- `query`
- `top_k`
- `trace_id`
- `allowed_source_filenames`
- opcionalmente `active_document_id`
- opcionalmente `active_document_title`
- opcionalmente `active_corpus`
- opcionalmente `last_source_intent`

### Representación de `retrieval_status`

Estados observados en runtime y RAG:

- `EVIDENCE_FOUND`
- `NO_EVIDENCE`
- `NO_EVIDENCE_FOR_ANSWER`
- `DISABLED`
- `unknown`
- `RAG_ERROR` pendiente de confirmar como valor público estable

Normalización observada:

- `NO_EVIDENCE` y `NO_EVIDENCE_FOR_ANSWER` se tratan como estados de safe refusal
- el runtime normaliza hacia `NO_EVIDENCE_FOR_ANSWER` en la superficie pública cuando corresponde

### Transporte de evidencia

La evidencia viaja mediante:

- `chunks`
- `chunk_ids`
- `document_ids`
- `source_filenames`
- `candidate_filenames`
- `selected_filenames`
- `scores`
- `ranking_scores`

En safe refusal, el runtime limpia evidencia pública si detecta que no es fiable.

### Diferencia entre evidencia encontrada y no encontrada

#### Evidencia encontrada

Caso nominal:

- `retrieval_status == "EVIDENCE_FOUND"`
- puede haber `chunk_ids`, `document_ids`, `source_filenames`
- suele producir `answer_mode="documentary_answer"`

#### No evidencia

Caso de safe refusal:

- `retrieval_status` cae en `NO_EVIDENCE` o `NO_EVIDENCE_FOR_ANSWER`
- `fallback_used=True`
- la respuesta evita generación libre
- la evidencia pública puede limpiarse a listas vacías

### Contrato implícito

- el runtime no confía ciegamente en el primer resultado de retrieval;
- puede degradar un `EVIDENCE_FOUND` a `NO_EVIDENCE_FOR_ANSWER` si la respuesta final del modelo es solo el marcador o si los chunks no pasan ciertas comprobaciones.

### Riesgo de drift

- local y remoto comparten intención, pero no necesariamente exactamente los mismos `warnings`;
- `app/rag_client.py` puede devolver `warnings` como lista de diccionarios, mientras que la persistencia de runs normaliza `warnings` a `list[str]`;
- la forma exacta de `RAG_ERROR` como contrato público estable queda pendiente de confirmar.

## 6. Contrato de métricas

### Módulos implicados

- `app/chat_runtime.py`
- `app/adapters/ollama_client.py`
- `app/adapters/openai_client.py`
- `app/observability/chat_runs.py`

### Campos observados en código

#### Públicos en `ChatResponse`

- `trace_id`
- `latency_ms`
- `prompt_eval_count`
- `eval_count`
- `prompt_eval_duration`
- `eval_duration`
- `total_duration`
- `load_duration`
- `fallback_used`

#### Internos o persistidos, pero no públicos en `ChatResponse`

- `tokens_input`
- `tokens_output`
- `tokens_total`
- `generation_latency_ms`
- `retrieval_latency_ms`
- `error_type`

#### No observado en el runtime actual

- `estimated_cost`

### Fiabilidad por proveedor

| Campo | Ollama local | OpenAI gestionado | Observación |
| --- | --- | --- | --- |
| `trace_id` | Sí | Sí | Se genera en runtime, no depende del proveedor |
| `latency_ms` | Sí | Sí | En OpenAI viene del adaptador; en runtime puede recomputarse |
| `prompt_eval_count` | Sí | No observado | Ollama lo devuelve nativamente |
| `eval_count` | Sí | No observado | Ollama lo devuelve nativamente |
| `tokens_input` | Implícito | No fiable | Runtime lo deriva desde `prompt_eval_count` |
| `tokens_output` | Implícito | No fiable | Runtime lo deriva desde `eval_count` |
| `tokens_total` | Derivable | Normalmente ausente | Runtime lo suma si existen entrada y salida |
| `prompt_eval_duration` | Sí | No observado | Métrica nativa Ollama |
| `eval_duration` | Sí | No observado | Métrica nativa Ollama |
| `total_duration` | Sí | No observado | Métrica nativa Ollama |
| `load_duration` | Sí | No observado | Métrica nativa Ollama |
| `fallback_used` | Sí | Sí | Lo decide el runtime |
| `error_type` | Persistido/logueado | Persistido/logueado | No sale en `ChatResponse` |
| `temperature_ignored` | Normalmente `False` | Puede ser `True` | OpenAI reintenta sin temperatura si la rechaza |

### Contrato observado

- `app/chat_runtime.py` recoge métricas del adaptador en `llm_metrics`
- `tokens_input = prompt_eval_count`
- `tokens_output = eval_count`
- `tokens_total` se toma del adaptador si existe; si no, se deriva como suma
- `error_type` se persiste como alias de `error_code`

### Contrato implícito

- `tokens_input` y `tokens_output` no son verdaderamente agnósticos al proveedor en el runtime actual;
- en la práctica dependen de que existan `prompt_eval_count` y `eval_count`.

### Riesgo de drift

- parte de la observabilidad crítica vive en runs persistidos, no en `ChatResponse`;
- OpenAI devuelve menos señales que Ollama;
- `estimated_cost` aparece en documentación de refactor, pero no en código del runtime observado.

## 7. Contrato de dependencias

### Módulos implicados

- `app/chat/dependencies.py`
- `app/chat/service.py`
- `app/chat_runtime.py`
- `app/main.py`

### Contrato observado

`ChatDependencies` define estas dependencias inyectables:

- `ask_chat`
- `build_document_prompt`
- `query_remote_rag`
- `resolve_provider_model`
- `save_chat_run`
- `log_event`
- `new_trace_id`
- `settings`
- `create_document_tool` opcional

`app/main.py` construye la implementación por defecto con `_build_chat_dependencies()`.

### Implementaciones por defecto observadas

En `app/chat_runtime.py`, `_dependency_or_default(...)` aplica esta regla:

- si `dependencies is None`, usa la función importada en el módulo;
- si el atributo inyectado es `None`, también usa la implementación por defecto;
- si hay valor, usa el inyectado.

### Qué se puede sustituir en tests

Observado en tests:

- `ChatServiceTests` inyecta todas las dependencias manualmente;
- otros tests siguen parcheando símbolos viejos en `app.main`:
  - `app.main.ask_chat`
  - `app.main.build_document_prompt`
  - `app.main.query_remote_rag`
  - `app.main.resolve_provider_model`
  - `app.main.create_document_tool`

### Qué riesgo introduce para el grafo runtime

- el grafo por defecto describe la ejecución nominal;
- pero `ChatDependencies` permite rutas alternativas en tests o refactors parciales;
- además, el runtime mantiene imports directos de compatibilidad, así que conviven dos formas de sustitución:
  - inyección explícita;
  - monkey patch de símbolos importados.

### Caminos alternativos observables

- `ChatService -> app.chat_runtime.run_chat_request(..., dependencies=...)`
- `app.main.run_chat_request(...) -> _build_chat_service()`
- tests que parchean `app.main.*`
- tests de `/creardoc` que parchean tanto `app.main.create_document_tool` como `app.chat_runtime.create_document_tool`

### Contrato implícito

- el proyecto está en una fase transicional: nuevo camino con `ChatDependencies`, pero compatibilidad mantenida con imports directos y parches antiguos.

### Riesgo de drift

- si se elimina una importación directa demasiado pronto, pueden romperse tests que aún parchean `app.main`;
- si se duplica la fuente de verdad entre dependencias inyectadas e imports legacy, el comportamiento puede divergir.

## 8. Riesgos de drift

### 1. `model` opcional en schema pero obligatorio en runtime

- **Descripción:** `ChatRequest` permite `model=None`, pero `app/chat_runtime.py` responde `400 model_required`.
- **Ruta:** `app/schemas.py`, `app/chat_runtime.py`
- **Impacto:** el contrato público estructural no refleja el contrato operativo real.
- **Mitigación mínima:** documentar expresamente que `model` es obligatorio para `POST /chat`.
- **Riesgo de tocarlo:** medio; cambiar el schema puede romper clientes o tests.

### 2. Contrato de error no modelado con Pydantic

- **Descripción:** `routes_chat.py` declara `response_model=ChatResponse`, pero los errores salen como `HTTPException.detail`.
- **Ruta:** `app/api/routes_chat.py`, `app/chat_runtime.py`, `app/schemas.py`
- **Impacto:** el contrato de error no está tipado igual que el de éxito.
- **Mitigación mínima:** documentar el payload de error observado y mantenerlo estable.
- **Riesgo de tocarlo:** medio; muchos tests y clientes pueden depender del shape actual.

### 3. Métricas persistidas pero no devueltas

- **Descripción:** `tokens_input`, `tokens_output`, `tokens_total`, `generation_latency_ms`, `retrieval_latency_ms`, `error_type` se persisten pero no salen en `ChatResponse`.
- **Ruta:** `app/chat_runtime.py`, `app/observability/chat_runs.py`, `app/schemas.py`
- **Impacto:** la respuesta pública y el artefacto persistido no tienen la misma observabilidad.
- **Mitigación mínima:** documentar claramente qué vive en response y qué vive en run.
- **Riesgo de tocarlo:** bajo si solo se documenta; medio si se intenta alinear contratos.

### 4. Ollama y OpenAI no exponen el mismo nivel métrico

- **Descripción:** Ollama devuelve métricas nativas ricas; OpenAI no.
- **Ruta:** `app/adapters/ollama_client.py`, `app/adapters/openai_client.py`
- **Impacto:** comparaciones entre proveedores pueden inducir conclusiones incorrectas.
- **Mitigación mínima:** comparar por `provider` y no asumir simetría de métricas.
- **Riesgo de tocarlo:** bajo documentalmente; alto si se fuerza una falsa uniformidad.

### 5. Diferencia entre RAG local y remoto

- **Descripción:** ambos comparten intención, pero el cliente remoto puede degradar a `NO_EVIDENCE_FOR_ANSWER` y los `warnings` no necesariamente tienen la misma forma.
- **Ruta:** `app/chat_runtime.py`, `app/rag_client.py`, `rag_service/main.py`
- **Impacto:** posible divergencia sutil en payloads de retrieval.
- **Mitigación mínima:** fijar y documentar el vocabulario público mínimo de retrieval.
- **Riesgo de tocarlo:** medio.

### 6. `warnings` heterogéneos

- **Descripción:** `ChatResponse` permite `list[str | dict]`, pero `chat_runs.py` normaliza `warnings` como `list[str]`.
- **Ruta:** `app/schemas.py`, `app/rag_client.py`, `app/observability/chat_runs.py`
- **Impacto:** parte de la semántica de warnings puede perderse en persistencia.
- **Mitigación mínima:** documentar la pérdida o cerrar un formato único.
- **Riesgo de tocarlo:** medio.

### 7. Tests que aún parchean símbolos legacy en `app.main`

- **Descripción:** varias pruebas no sustituyen dependencias vía `ChatDependencies`, sino con `patch("app.main....")`.
- **Ruta:** `tests/test_chat_service.py`, `tests/test_remote_rag_service.py`, `tests/test_rag_no_evidence_contract.py`, `tests/test_chat_create_document_command.py`
- **Impacto:** refactors internos pueden romper tests aunque el contrato funcional siga igual.
- **Mitigación mínima:** preservar compatibilidad durante hardening y revisar tests antes de mover imports.
- **Riesgo de tocarlo:** alto si se cambian imports o wiring sin una transición controlada.

### 8. Duplicidad entre `chat_trace.py` y `chat_runs.py`

- **Descripción:** la documentación y los cargadores operativos actuales apuntan a `chat_runs.py` como fuente viva, pero `chat_trace.py` sigue existiendo.
- **Ruta:** `app/observability/chat_runs.py`, `app/observability/chat_trace.py`, `docs/OBSERVABILITY.md`, `docs/TECH_DEBT_AND_RISKS.md`
- **Impacto:** ambigüedad sobre el almacén canónico.
- **Mitigación mínima:** documentar qué almacén es operativo hoy.
- **Riesgo de tocarlo:** medio.

## 9. Checklist de hardening

- [ ] Mantener compatibilidad estructural de `ChatRequest`.
- [ ] Mantener compatibilidad estructural de `ChatResponse`.
- [ ] No perder `trace_id` cuando falte en request.
- [ ] Mantener `retrieval_status` con vocabulario público estable.
- [ ] Mantener `chunk_ids` en respuestas con evidencia y limpiarlos en safe refusal.
- [ ] Mantener `source_filenames` en respuestas documentales y safe refusal.
- [ ] Mantener `latency_ms` en toda respuesta exitosa.
- [ ] No romper el mapeo actual de errores HTTP esperados.
- [ ] Preservar el contrato de `invalid_provider_model_pair`.
- [ ] Preservar el contrato de `model_required`.
- [ ] No romper la degradación controlada del RAG remoto a `NO_EVIDENCE_FOR_ANSWER`.
- [ ] Mantener la persistencia de runs aunque la respuesta pública no incluya todas las métricas.
- [ ] Preservar tests existentes que parchean `app.main`.
- [ ] No romper tests que parchean `app.chat_runtime.create_document_tool`.
- [ ] No asumir que OpenAI y Ollama ofrecen la misma granularidad métrica.

## 10. Relación con `runtime_graph.json`

Los nodos y aristas más dependientes de estos contratos son:

### Entrada y contrato HTTP

- nodo `endpoint:POST /chat`
- nodo `app/api/routes_chat.py`
- nodo `app/schemas.py`
- arista `app/api/routes_chat.py -> endpoint:POST /chat`
- arista `app/api/routes_chat.py -> app/schemas.py`

Si cambia `ChatRequest` o la forma de error, estas aristas siguen existiendo, pero el significado contractual cambia.

### Orquestación del runtime

- nodo `app/main.py`
- nodo `app/chat/service.py`
- nodo `app/chat/dependencies.py`
- nodo `app/chat_runtime.py`
- aristas:
  - `app/main.py -> app/chat/service.py`
  - `app/chat/service.py -> app/chat_runtime.py`
  - `app/chat_runtime.py -> app/chat/dependencies.py`

Si cambia `ChatDependencies`, el grafo nominal puede seguir siendo igual, pero los caminos efectivos en tests pueden divergir.

### Contrato proveedor/modelo

- nodo `app/llm_client.py`
- nodos `app/adapters/ollama_client.py`, `app/adapters/openai_client.py`
- nodos `provider:ollama`, `provider:openai`
- aristas:
  - `app/chat_runtime.py -> app/llm_client.py`
  - `app/llm_client.py -> app/adapters/ollama_client.py`
  - `app/llm_client.py -> app/adapters/openai_client.py`

Si cambia la política `provider/model`, estas aristas siguen, pero cambia el contrato semántico del runtime.

### Contrato RAG

- nodo `app/rag_client.py`
- nodo `DB/chunks/document_context.py`
- nodo `rag_service/main.py`
- nodo `endpoint:POST /rag/query`
- aristas:
  - `app/chat_runtime.py -> app/rag_client.py`
  - `app/chat_runtime.py -> DB/chunks/document_context.py`
  - `app/rag_client.py -> endpoint:POST /rag/query`
  - `rag_service/main.py -> DB/chunks/document_context.py`

Estas aristas dependen del contrato de `retrieval_status`, `chunk_ids`, `document_ids` y `source_filenames`.

### Observabilidad

- nodo `app/observability/trace.py`
- nodo `app/observability/logging.py`
- nodo `app/observability/chat_runs.py`
- nodo `database:CHAT_RUNS/`
- aristas:
  - `app/chat_runtime.py -> app/observability/trace.py`
  - `app/chat_runtime.py -> app/observability/logging.py`
  - `app/chat_runtime.py -> app/observability/chat_runs.py`
  - `app/observability/chat_runs.py -> database:CHAT_RUNS/`

Estas aristas dependen directamente de que no se pierdan `trace_id`, `status`, `retrieval_status`, errores y métricas internas.

## Relacionado

- [[RUNTIME_FLOW]]
- [[RUNTIME_GRAPH]]
- [[ARCHITECTURE]]
- [[RAG_AND_EVIDENCE]]
- [[OBSERVABILITY]]
- [[TECH_DEBT_AND_RISKS]]
- [[contracts/chat_runtime_refactor_contract|contracts/chat_runtime_refactor_contract.md]]
- [[GLOSSARY]]
