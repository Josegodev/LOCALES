# Chat Evals Foundation

Los chat evals apuntan al runtime `POST /chat`, no a Telegram.

## Archivos

- Los casos viven en `evals/cases/chat_cases.json`.
- Los baselines viven en `evals/baselines/chat_baseline.json`.
- Las ejecuciones escriben resultados en `evals/runs/`.

## Arranque requerido

Backend:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Ejecutar evals

```bash
python scripts/run_chat_evals.py --base-url http://127.0.0.1:8000
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
