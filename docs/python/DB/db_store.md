# DB/db_store.py

## Rol

Módulo del laboratorio SQLite de persistencia y memoria aprobada.

## Identidad técnica

- Ruta real: `DB/db_store.py`
- Tipo: `db_lab`
- Ámbito: `laboratorio SQLite de memoria`
- Módulo lógico: `DB.db_store`

## Símbolos principales

- Funciones: `now_iso`, `sha256_text`, `byte_len`, `safe_slug`, `read_schema`, `connect_sqlite`, `compact_db`, `db_total_size_bytes`, `init_registry`, `get_profile_dir`, `get_raw_db_path`, `get_memory_db_path`, `create_model_profile`, `ensure_profile_exists`, `list_model_profiles`, `save_exchange`, `approve_memory`, `get_memory_context`, `pin_prompt`, `enforce_memory_limit`
- Funciones adicionales: `3` más.

## Dependencias internas directas

- No se han detectado imports internos directos del repositorio.

## Dependencias inversas

- [[python/DB/approve_memory|DB/approve_memory.py]]: depende de este archivo vía `db_store.approve_memory`.
- [[python/DB/prune|DB/prune.py]]: depende de este archivo vía `db_store.memory_stats`, `db_store.prune_raw`, `db_store.raw_stats`.
- [[python/DB/setup_profile|DB/setup_profile.py]]: depende de este archivo vía `db_store.create_model_profile`.

## Imports externos observados

- Paquetes o módulos externos detectados: `datetime`, `hashlib`, `json`, `pathlib`, `sqlite3`, `typing`

## Relación dentro del sistema

- Pertenece al laboratorio SQLite de memoria y persistencia manual.

## Observaciones

- Sin observaciones adicionales relevantes a partir del análisis estático actual.

## Relacionado

- [[python/DB/INDEX]]
- [[COMPONENT_MAP]]
- [[GLOSSARY]]
