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