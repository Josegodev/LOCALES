# Chat Evals Foundation

Los chat evals apuntan al runtime `POST /chat`, no a Telegram.

## Archivos

- Los casos viven en `evals/cases/chat_cases.json`.
- Los baselines viven en `evals/baselines/chat_baseline.json`.
- Las ejecuciones escriben resultados en `evals/runs/`.

## Endpoint real

- El frontend local del repo ahora llama a `POST /api/evals/chat/run`.
- Ese endpoint ejecuta `app.chat_eval_runner.run_chat_evals(...)`.
- `GET /api/evals/chat` queda como compatibilidad para listar trazas de chat, no ejecuta evals.
- Las runtime traces siguen en `data/chat_traces.jsonl`.
- Los eval runs persistidos siguen separados en `evals/runs/`.

## Arranque requerido

Backend:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Ejecutar evals

```bash
python scripts/run_chat_evals.py --base-url http://127.0.0.1:8000
```

Comando E2E del endpoint real usado por el frontend:

```bash
bash scripts/run_chat_eval_e2e.sh
```

Ese comando levanta una instancia aislada del backend actual en `127.0.0.1:8011`, ejecuta `POST /api/evals/chat/run` y la cierra al terminar.

Opcional para reutilizar un backend ya arrancado:

```bash
START_BACKEND=0 BASE_URL=http://127.0.0.1:8000 bash scripts/run_chat_eval_e2e.sh
```

## Que mide

- `status`
- `retrieval_status`
- presencia de `source_filenames`
- minimo de `chunk_ids`
- terminos requeridos en la respuesta
- terminos prohibidos en la respuesta
- modos de fallo operacionales permitidos

## Que no mide

- no fija el texto exacto generado
- no calcula metricas avanzadas de calidad
- no crea dashboard
- no programa ejecuciones automaticas
- no toca Telegram

## Salida

- Los runs se escriben en `evals/runs/`.
- Puedes verlos con `ls -lt evals/runs/`.

## Advertencias

- El texto exacto del modelo no debe fijarse como baseline.
- Los evals comparan contratos minimos, no equivalencia semantica completa.
- Las runtime traces y los eval runs son artefactos separados.
