# Reglas de separacion runtime vs experimentacion

- `app/` y `scripts/run_telegram.py` se consideran runtime estable.
- `llm_lab/` y `DB/` se consideran espacio de experimentacion local.
- No conectar automaticamente cambios de `llm_lab/` al flujo runtime.
- No arrancar servicios de pruebas desde scripts de integracion Codex.
- Cualquier cambio que mueva reglas de laboratorio a runtime debe justificarse como `CRITICO`.
