# Chat Evals Foundation

Los evals estan preparados, pero todavia no son ejecutables.

- Los chat evals deben apuntar directamente a `POST /chat`.
- Los Telegram evals han sido eliminados.
- Los casos viven en `evals/cases/chat_cases.json`.
- Los baselines viven en `evals/baselines/chat_baseline.json`.
- Las futuras ejecuciones deben escribir en `evals/runs/`.
- Un futuro runner debe comparar la salida real de `/chat` contra el contrato de casos y baseline.
- El texto exacto generado por el modelo no debe fijarse como baseline.
