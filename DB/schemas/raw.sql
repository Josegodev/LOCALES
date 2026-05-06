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