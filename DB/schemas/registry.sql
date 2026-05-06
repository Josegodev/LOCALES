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