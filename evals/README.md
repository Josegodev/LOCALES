# Evals de chat para LOCALES

## Que mide

Esta carpeta mide drift semantico operacional del camino `FastAPI /chat -> Ollama`
con reglas deterministas y reproducibles.

Mide:

- si el endpoint responde con HTTP correcto
- si la respuesta no esta vacia
- si contiene terminos esperados
- si evita terminos prohibidos
- si la longitud se mantiene dentro de contrato
- si las metricas reales de Ollama siguen en rangos razonables
- si el comportamiento actual cambia frente a un baseline anterior

## Que NO mide

No mide:

- calidad semantica profunda
- veracidad factual
- calidad de razonamiento
- calidad de recuperacion RAG
- preferencias de estilo

No usa:

- LLM judge
- embeddings
- otro modelo para evaluar

## Por que este metodo es util

Este metodo sirve en HARDENING porque:

- es explicable
- es reproducible
- no introduce nuevas dependencias
- permite detectar drift visible en contratos operativos

## Requisitos previos

### Backend

Levantar FastAPI:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Variables

- `BACKEND_URL`
  - default: valor local por defecto definido en `app/config.py`
- `LOCALES_BACKEND_URL`
  - legado; se usa solo como fallback si `BACKEND_URL` no está definido
- `EVAL_TIMEOUT_SECONDS`
  - default: `60`
- `OLLAMA_MODEL`
  - se usa como metadata del run cuando esta disponible

## Como lanzar evals

Ejecucion normal:

```bash
python scripts/run_chat_evals.py
```

Escritura de baseline:

```bash
python scripts/run_chat_evals.py --write-baseline
```

Importante:

- no uses un baseline con casos fallidos
- el runner no escribe baseline si la ejecucion actual tiene fallos

Comparacion contra baseline:

```bash
python scripts/run_chat_evals.py --compare-baseline
```

En este repo, si `python` no esta en `PATH`, usa:

```bash
.venv/bin/python scripts/run_chat_evals.py
```

## Archivos generados

Cada ejecucion genera:

- `evals/runs/chat_eval_<timestamp>.json`

Cada run guarda:

- `run_id`
- `created_at`
- `backend_url`
- `model`
- `cases_total`
- `cases_passed`
- `cases_failed`
- `results`
- metricas agregadas
- comparacion con baseline cuando se pide

## Como escribir casos

Cada caso en `evals/cases/chat_cases.json` debe incluir:

- `id`
- `input`
- `expected_contains`
- `forbidden_contains`
- `min_chars`
- `max_chars`
- `notes`

## Como funciona la comparacion con baseline

La comparacion detecta:

- cambio de `status`
- cambio de `pass/fail`
- cambio de longitud mayor del 40%
- respuesta vacia
- terminos prohibidos nuevos
- cambio de latencia mayor del 100%
- aumento de prompt tokens mayor del 50%
- aumento de output tokens mayor del 100%
- degradacion de tokens/s mayor del 50%
- aumento de `total_duration` mayor del 100%
- respuestas extremadamente largas

## Metricas: latencia total vs velocidad de generacion

`latency_ms` es el tiempo total observado por el backend para completar la llamada de
chat.

`output_tokens_per_second` y `prompt_tokens_per_second` miden velocidad de proceso,
no tiempo total.

Una respuesta puede tener:

- latencia total alta
- pero buena velocidad de generacion

o al reves.

## Metricas: prompt tokens vs output tokens

- `prompt tokens`
  - tokens consumidos al procesar la entrada y el contexto
- `output tokens`
  - tokens generados en la respuesta

El crecimiento de prompt tokens es importante porque suele indicar:

- mas contexto
- prompts mas largos
- inflation del contexto
- mayor coste temporal por llamada

## Riesgo de context inflation

`context inflation` significa que el sistema empieza a enviar cada vez mas contexto al
modelo para responder a preguntas parecidas.

Eso es un riesgo operacional porque puede producir:

- mas latencia
- mas tokens de entrada
- menor throughput
- mayor variabilidad

## Limitaciones del metodo

Este metodo es intencionalmente simple.

Limitaciones:

- no decide si una respuesta es “buena” en sentido humano
- no reemplaza pruebas manuales
- no detecta toda regresion semantica
- depende de casos bien escogidos
- si el corpus RAG cambia, algunos casos pueden requerir ajuste
