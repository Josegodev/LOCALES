# Flujo: perfiles, raw output y memoria aprobada

```text
POST /profiles o setup_profile.py
  -> DB/db_store.create_model_profile()
  -> registry.sqlite + profiles/<slug>/{raw,memory}.sqlite

POST /chat o chat_once.py
  -> ensure_profile_exists()
  -> get_memory_context()
  -> LM Studio
  -> save_exchange()

approve_memory.py o POST /profiles/{slug}/memory/approve
  -> approve_memory()
  -> memory.sqlite
```

## Contratos

- `slug` se normaliza con `safe_slug`.
- `raw_outputs.status` solo acepta `ok` o `error`.
- Memoria persistente solo entra por aprobacion explicita de output `ok`.

## Riesgos

- `approve_memory()` valida existencia de output en raw DB, pero `memory.sqlite` no tiene foreign key hacia `raw.sqlite` porque son bases separadas.
- Si LM Studio falla, se guarda intercambio con `status=error` y `model_output=None`.
