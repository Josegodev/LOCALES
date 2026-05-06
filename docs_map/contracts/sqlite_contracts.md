# Contratos SQLite

## `DB/schemas/memory.sql`
```sql
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

INSERT OR IGNORE INTO schema_meta (key, value)
VALUES ('schema_version', '1');

CREATE TABLE IF NOT EXISTS memory_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    created_at TEXT NOT NULL,

    source_output_id INTEGER NOT NULL,
    source_output_hash TEXT NOT NULL,

    saved_text TEXT NOT NULL
        CHECK (length(trim(saved_text)) > 0),

    saved_text_hash TEXT NOT NULL UNIQUE,

    reason TEXT,

    active INTEGER NOT NULL DEFAULT 1
        CHECK (active IN (0,1))
);

CREATE INDEX IF NOT EXISTS idx_memory_items_created_at
ON memory_items(created_at);

CREATE INDEX IF NOT EXISTS idx_memory_items_active
ON memory_items(active);

CREATE INDEX IF NOT EXISTS idx_memory_items_source_hash
ON memory_items(source_output_hash);
```

## `DB/schemas/raw.sql`
```sql
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

INSERT OR IGNORE INTO schema_meta (key, value)
VALUES ('schema_version', '1');

CREATE TABLE IF NOT EXISTS raw_prompts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,

    user_prompt TEXT NOT NULL
        CHECK (length(trim(user_prompt)) > 0),

    prompt_hash TEXT NOT NULL,
    prompt_bytes INTEGER NOT NULL
        CHECK (prompt_bytes >= 0),

    pinned INTEGER NOT NULL DEFAULT 0
        CHECK (pinned IN (0,1))
);

CREATE TABLE IF NOT EXISTS raw_outputs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    prompt_id INTEGER NOT NULL,

    created_at TEXT NOT NULL,

    model_output TEXT,
    output_hash TEXT,
    output_bytes INTEGER NOT NULL DEFAULT 0
        CHECK (output_bytes >= 0),

    request_json TEXT NOT NULL,
    response_json TEXT,

    status TEXT NOT NULL
        CHECK (status IN ('ok', 'error')),

    error_text TEXT,

    approved_for_memory INTEGER NOT NULL DEFAULT 0
        CHECK (approved_for_memory IN (0,1)),

    FOREIGN KEY(prompt_id)
        REFERENCES raw_prompts(id)
        ON DELETE CASCADE,

    CHECK (
        status = 'error'
        OR (
            model_output IS NOT NULL
            AND length(trim(model_output)) > 0
            AND output_hash IS NOT NULL
        )
    )
);

CREATE INDEX IF NOT EXISTS idx_raw_prompts_created_at
ON raw_prompts(created_at);

CREATE INDEX IF NOT EXISTS idx_raw_prompts_expires_at
ON raw_prompts(expires_at);

CREATE INDEX IF NOT EXISTS idx_raw_outputs_prompt_id
ON raw_outputs(prompt_id);

CREATE INDEX IF NOT EXISTS idx_raw_outputs_status
ON raw_outputs(status);

CREATE INDEX IF NOT EXISTS idx_raw_outputs_output_hash
ON raw_outputs(output_hash);

CREATE INDEX IF NOT EXISTS idx_raw_outputs_approved
ON raw_outputs(approved_for_memory);
```

## `DB/schemas/registry.sql`
```sql
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

INSERT OR IGNORE INTO schema_meta (key, value)
VALUES ('schema_version', '1');

CREATE TABLE IF NOT EXISTS model_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    slug TEXT NOT NULL UNIQUE,

    runtime TEXT NOT NULL,
    model_name TEXT NOT NULL,

    parameters_json TEXT NOT NULL DEFAULT '{}',
    system_prompt TEXT NOT NULL DEFAULT '',

    raw_retention_days INTEGER NOT NULL DEFAULT 14
        CHECK (raw_retention_days > 0),

    raw_max_rows INTEGER NOT NULL DEFAULT 500
        CHECK (raw_max_rows > 0),

    raw_max_mb INTEGER NOT NULL DEFAULT 200
        CHECK (raw_max_mb > 0),

    memory_max_items INTEGER NOT NULL DEFAULT 200
        CHECK (memory_max_items > 0),

    created_at TEXT NOT NULL,

    active INTEGER NOT NULL DEFAULT 1
        CHECK (active IN (0,1))
);

CREATE INDEX IF NOT EXISTS idx_model_profiles_slug
ON model_profiles(slug);

CREATE INDEX IF NOT EXISTS idx_model_profiles_active
ON model_profiles(active);
```

## Bases detectadas
- `DB/chunks/documents.sqlite` (1.0 MB)
  - Tablas: chunks, documents
  - Indices: idx_chunks_document_id
  - Filas `chunks`: 261
  - Filas `documents`: 66
- `DB/documents.sqlite` (0 B)
  - Estado: EMPTY_OR_MISSING
- `DB/profiles/lmstudio_granite32_8b_temp00/memory.sqlite` (36.0 KB)
  - Tablas: memory_items, schema_meta
  - Indices: idx_memory_items_active, idx_memory_items_created_at, idx_memory_items_source_hash
  - Filas `memory_items`: 1
  - Filas `schema_meta`: 1
- `DB/profiles/lmstudio_granite32_8b_temp00/raw.sqlite` (60.0 KB)
  - Tablas: raw_outputs, raw_prompts, schema_meta
  - Indices: idx_raw_outputs_approved, idx_raw_outputs_output_hash, idx_raw_outputs_prompt_id, idx_raw_outputs_status, idx_raw_prompts_created_at, idx_raw_prompts_expires_at
  - Filas `raw_outputs`: 8
  - Filas `raw_prompts`: 8
  - Filas `schema_meta`: 1
- `DB/profiles/lmstudio_qwen35_9b_q4km_temp02/memory.sqlite` (36.0 KB)
  - Tablas: memory_items, schema_meta
  - Indices: idx_memory_items_active, idx_memory_items_created_at, idx_memory_items_source_hash
  - Filas `memory_items`: 4
  - Filas `schema_meta`: 1
- `DB/profiles/lmstudio_qwen35_9b_q4km_temp02/raw.sqlite` (136.0 KB)
  - Tablas: raw_outputs, raw_prompts, schema_meta
  - Indices: idx_raw_outputs_approved, idx_raw_outputs_output_hash, idx_raw_outputs_prompt_id, idx_raw_outputs_status, idx_raw_prompts_created_at, idx_raw_prompts_expires_at
  - Filas `raw_outputs`: 9
  - Filas `raw_prompts`: 9
  - Filas `schema_meta`: 1
- `DB/profiles/lmstudio_qwen35_9b_q4km_temp07/memory.sqlite` (36.0 KB)
  - Tablas: memory_items, schema_meta
  - Indices: idx_memory_items_active, idx_memory_items_created_at, idx_memory_items_source_hash
  - Filas `memory_items`: 0
  - Filas `schema_meta`: 1
- `DB/profiles/lmstudio_qwen35_9b_q4km_temp07/raw.sqlite` (100.0 KB)
  - Tablas: raw_outputs, raw_prompts, schema_meta
  - Indices: idx_raw_outputs_approved, idx_raw_outputs_output_hash, idx_raw_outputs_prompt_id, idx_raw_outputs_status, idx_raw_prompts_created_at, idx_raw_prompts_expires_at
  - Filas `raw_outputs`: 7
  - Filas `raw_prompts`: 7
  - Filas `schema_meta`: 1
- `DB/registry.sqlite` (32.0 KB)
  - Tablas: model_profiles, schema_meta
  - Indices: idx_model_profiles_active, idx_model_profiles_slug
  - Filas `model_profiles`: 3
  - Filas `schema_meta`: 1

## Observaciones de hardening
- `DB/db_store.py` activa `PRAGMA foreign_keys`, `journal_mode=WAL` y `busy_timeout=5000`.
- `raw_outputs` exige salida no vacia cuando `status=ok`.
- `memory_items.saved_text_hash` es `UNIQUE`, evita duplicados exactos por hash.
- NO_VERIFICADO: no se valida migracion incremental de schema mas alla de `schema_meta` version 1.
