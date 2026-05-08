# LOCALES HARDENING AUDIT

Fecha de auditoria: 2026-05-08
Fase: HARDENING
Alcance: `app/`, `scripts/run_telegram.py`, `tests/`

## 1. Estructura actual observada

### Flujo productivo real

El flujo Telegram actual no vive principalmente en `app/bot_service.py`.

- `scripts/run_telegram.py`
  - polling de Telegram
  - parseo de comandos `/doc` y `/doc_ai`
  - autorizacion Telegram
  - llamada al backend FastAPI
  - llamada al LLM para generar Markdown
  - logs operativos
- `app/main.py`
  - endpoint `/documents`
  - endpoint `/chat`
- `app/document_writer.py`
  - escritura final del documento
- `app/llm_client.py`
  - generacion de Markdown para `/doc_ai`
- `app/lmstudio_client.py`
  - cliente del chat RAG actual

### Contradiccion detectada

`app/bot_service.py` sugiere ser el servicio principal del bot, pero en el estado auditado solo contenia `build_llm_prompt()`. El flujo real estaba concentrado en `scripts/run_telegram.py`.

Clasificacion: `CRITICO`

Motivo:
- el nombre del modulo no coincide con la responsabilidad real
- dificulta localizar contratos
- favorece drift entre script, backend y writer

## 2. Problemas de acoplamiento

### Acoplamiento 1: script con demasiadas responsabilidades

`scripts/run_telegram.py` mezclaba:
- transporte Telegram
- parseo de comandos
- autorizacion
- contrato HTTP hacia FastAPI
- llamada al LLM
- validacion de salida
- logging

Riesgo:
- una pequena correccion puede romper varias capas a la vez
- testing mas costoso porque todo depende del mismo archivo

Clasificacion: `CRITICO`

### Acoplamiento 2: observabilidad heterogenea

Habia logs JSON en algunos puntos y `print()` libres en otros.

Riesgo:
- no hay una traza estable por mensaje
- cuesta correlacionar Telegram -> FastAPI -> writer

Clasificacion: `CRITICO`

### Acoplamiento 3: proveedor LLM duplicado por zonas

El repo usa varias rutas:
- `app/llm_client.py`
- `app/lmstudio_client.py`
- clientes LM Studio dentro de `DB/`
- soporte Ollama en `llm_lab/`

Riesgo:
- contratos distintos para proveedores parecidos
- defaults distintos segun modulo
- drift de configuracion

Clasificacion: `CRITICO`

Nota:
No se toca `llm_lab/` en esta iteracion. Solo se registra como superficie de drift.

## 3. Superficie de fallo

### Entrada Telegram
- mensaje vacio
- `user_id` ausente
- `chat_id` ausente
- comando mal formado

### Politica local
- `TELEGRAM_ALLOWED_USER_IDS` invalido
- usuario no autorizado

### LLM local
- timeout
- proceso no disponible
- respuesta HTTP no valida
- respuesta JSON mal formada
- `content` ausente o no texto

### Backend local
- `/documents` devuelve 4xx o 5xx
- respuesta no JSON

### Persistencia
- nombre de archivo invalido
- path traversal
- extension no permitida
- contenido vacio
- archivo ya existente

## 4. Piezas reutilizables

Estas piezas ya estaban razonablemente aprovechables:

- `app/schemas.py`
  - contrato Pydantic para `CreateDocumentRequest`
- `app/document_writer.py`
  - validacion local y escritura segura
- `app/telegram_permissions.py`
  - cierre de autorizacion por user id
- `app/main.py:/documents`
  - frontera backend estable para escritura documental

Clasificacion: `INFORMATIVO`

## 5. Riesgos relevantes

### Riesgo de drift de configuracion

Hay dos mundos en paralelo:
- chat actual orientado a LM Studio
- objetivo de endurecimiento orientado a Ollama local

Si se cambia de proveedor sin shim de compatibilidad, el bot puede romperse aunque el codigo compile.

Clasificacion: `CRITICO`

### Riesgo de import ambiguo en el repo

Ya existen modulos con responsabilidades parecidas y nombres repetidos en otras carpetas (`DB/`, `llm_lab/`).

Clasificacion: `INFORMATIVO`

### Riesgo de trazabilidad parcial

El pipeline `/chat` sigue usando `app/lmstudio_client.py` y no comparte todavia el mismo nivel de observabilidad que `/doc_ai`.

Clasificacion: `INFORMATIVO`

No se amplifica este cambio en esta fase para no abrir un refactor mayor.

## 6. Propuesta minima incremental

### Objetivo

Separar sin reescribir.

### Corte minimo propuesto

- `app/contracts/`
  - modelos Pydantic del flujo Telegram
- `app/observability/`
  - `trace_id`
  - logger JSON estructurado
- `app/adapters/`
  - Telegram HTTP
  - backend HTTP local
  - cliente LLM local compatible con Ollama
- `app/services/`
  - logica del bot y validaciones de comandos
- `scripts/run_telegram.py`
  - solo fachada de ejecucion y wiring

### Regla de migracion

Mover solo lo necesario para:
- aislar transporte
- cerrar contratos
- anadir trazabilidad
- mantener el comportamiento externo

### Cambios minimos aplicados en esta iteracion

1. Se crea `trace_id` por mensaje y se reutiliza como `request_id` en escritura documental.
2. Se unifica el logging en JSON estructurado.
3. Se separa el cliente LLM local en un adapter preparado para `OLLAMA_BASE_URL`, `OLLAMA_MODEL` y `OLLAMA_TIMEOUT_SECONDS`.
4. Se mantiene compatibilidad con el punto de entrada actual `scripts/run_telegram.py`.
5. No se mueve `DB/`.
6. No se toca `llm_lab/` mas alla de reconocer su drift.

## 7. Limites de esta iteracion

- No se modifica el contrato HTTP de `/chat`.
- No se integra runtime externo.
- No se cambia la persistencia.
- No se reorganiza `DB/`.
- No se introduce ningun framework de agentes.

## 8. Siguiente cambio recomendado

Siguiente paso mas importante despues de este corte:

Unificar el contrato del proveedor LLM productivo para que `/chat` y `/doc_ai` no dependan de clientes distintos con observabilidad distinta.

Estado: `PREMATURO`

Motivo:
- primero convenia cerrar trazabilidad y separacion local minima
- despues ya se puede decidir si conviene consolidar LM Studio y Ollama bajo un contrato comun

## 9. Unificacion del camino /chat sobre Ollama

### Que cambio

El endpoint `/chat` ya no llama a `app/lmstudio_client.py`.

Ahora el flujo queda asi:

- `scripts/run_telegram.py`
  - propaga `trace_id`, `user_id` y `chat_id` hacia FastAPI
- `app/adapters/backend_client.py`
  - envia esos campos al endpoint `/chat`
- `app/main.py`
  - usa la fachada `app/llm_client.py`
- `app/llm_client.py`
  - delega el chat a `app/adapters/ollama_client.py`
- `app/adapters/ollama_client.py`
  - llama a `http://127.0.0.1:11434/api/chat`
  - `stream=false`
  - `options.temperature=0.2`
  - `options.num_predict=300`

### Que se mantiene legacy

- `app/lmstudio_client.py` sigue existiendo como `legacy`.
- No se borra en esta iteracion para evitar un cambio mas grande del repo.
- `DB/` y `llm_lab/` no se tocan.

Clasificacion: `INFORMATIVO`

### Superficie de fallo

El camino `/chat` ahora falla de forma explicita en estos puntos:

- `llm_unavailable`
  - Ollama no responde o no esta levantado
- `llm_timeout`
  - Ollama supera `OLLAMA_TIMEOUT_SECONDS`
- `llm_invalid_json`
  - la respuesta no es JSON valido
- `llm_missing_content`
  - falta `message.content`
- `llm_model_not_available`
  - el modelo no existe o no esta disponible
- `llm_http_error`
  - error HTTP no clasificado

Clasificacion: `CRITICO`

### Observabilidad minima cerrada

Los logs del camino `/chat` incluyen:

- `event`
- `trace_id`
- `chat_id`
- `user_id`
- `model`
- `status`
- `latency_ms`
- `error_code` cuando aplica

Esto permite correlacionar:

- recepcion en Telegram
- llamada al endpoint `/chat`
- resultado del LLM

### Como probarlo localmente

1. Levantar Ollama local con el modelo:
   - `granite4.1:8b`
2. Exportar variables:
   - `OLLAMA_BASE_URL=http://127.0.0.1:11434`
   - `OLLAMA_MODEL=granite4.1:8b`
   - `OLLAMA_TIMEOUT_SECONDS=45`
3. Levantar FastAPI.
4. Enviar un mensaje normal al bot de Telegram.
5. Comprobar que:
   - el bot responde sin stacktrace
   - aparecen logs JSON con el mismo `trace_id`
   - no hay referencias activas a LM Studio en el camino `/chat`

### Validacion automatica

Ejecutar:

- `.venv/bin/python -m unittest discover -s tests`
