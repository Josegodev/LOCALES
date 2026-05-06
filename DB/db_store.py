import hashlib
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent

REGISTRY_DB = BASE_DIR / "registry.sqlite"
SCHEMAS_DIR = BASE_DIR / "schemas"
PROFILES_DIR = BASE_DIR / "profiles"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def byte_len(value: str | None) -> int:
    if value is None:
        return 0
    return len(value.encode("utf-8"))


def safe_slug(value: str) -> str:
    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
    cleaned = "".join(ch if ch in allowed else "_" for ch in value.strip())

    if not cleaned:
        raise ValueError("slug vacío")

    if cleaned.startswith("."):
        raise ValueError("slug inválido: no puede empezar por punto")

    if ".." in cleaned:
        raise ValueError("slug inválido: contiene '..'")

    return cleaned


def read_schema(name: str) -> str:
    path = SCHEMAS_DIR / name

    if not path.exists():
        raise FileNotFoundError(f"No existe el schema: {path}")

    return path.read_text(encoding="utf-8")


def connect_sqlite(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA busy_timeout = 5000;")
    return conn


def compact_db(path: Path) -> None:
    conn = connect_sqlite(path)
    try:
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
        conn.execute("VACUUM;")
    finally:
        conn.close()


def db_total_size_bytes(path: Path) -> int:
    total = path.stat().st_size if path.exists() else 0

    for suffix in ("-wal", "-shm"):
        extra = Path(str(path) + suffix)
        if extra.exists():
            total += extra.stat().st_size

    return total


def init_registry() -> None:
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)

    schema = read_schema("registry.sql")

    with connect_sqlite(REGISTRY_DB) as conn:
        conn.executescript(schema)


def get_profile_dir(slug: str) -> Path:
    return PROFILES_DIR / safe_slug(slug)


def get_raw_db_path(slug: str) -> Path:
    return get_profile_dir(slug) / "raw.sqlite"


def get_memory_db_path(slug: str) -> Path:
    return get_profile_dir(slug) / "memory.sqlite"


def create_model_profile(
    slug: str,
    model_name: str,
    runtime: str = "lmstudio",
    parameters: dict[str, Any] | None = None,
    system_prompt: str = "",
    raw_retention_days: int = 14,
    raw_max_rows: int = 500,
    raw_max_mb: int = 200,
    memory_max_items: int = 200,
) -> int:
    init_registry()

    clean_slug = safe_slug(slug)

    if not model_name.strip():
        raise ValueError("model_name vacío")

    if not runtime.strip():
        raise ValueError("runtime vacío")

    if raw_retention_days <= 0:
        raise ValueError("raw_retention_days debe ser > 0")

    if raw_max_rows <= 0:
        raise ValueError("raw_max_rows debe ser > 0")

    if raw_max_mb <= 0:
        raise ValueError("raw_max_mb debe ser > 0")

    if memory_max_items <= 0:
        raise ValueError("memory_max_items debe ser > 0")

    profile_dir = get_profile_dir(clean_slug)
    profile_dir.mkdir(parents=True, exist_ok=True)

    with connect_sqlite(get_raw_db_path(clean_slug)) as conn:
        conn.executescript(read_schema("raw.sql"))

    with connect_sqlite(get_memory_db_path(clean_slug)) as conn:
        conn.executescript(read_schema("memory.sql"))

    parameters_json = json.dumps(
        parameters or {},
        sort_keys=True,
        ensure_ascii=False,
    )

    with connect_sqlite(REGISTRY_DB) as conn:
        cursor = conn.execute(
            """
            INSERT INTO model_profiles (
                slug,
                runtime,
                model_name,
                parameters_json,
                system_prompt,
                raw_retention_days,
                raw_max_rows,
                raw_max_mb,
                memory_max_items,
                created_at,
                active
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """,
            (
                clean_slug,
                runtime.strip(),
                model_name.strip(),
                parameters_json,
                system_prompt,
                raw_retention_days,
                raw_max_rows,
                raw_max_mb,
                memory_max_items,
                now_iso(),
            ),
        )

        return int(cursor.lastrowid)


def ensure_profile_exists(slug: str) -> dict[str, Any]:
    init_registry()

    clean_slug = safe_slug(slug)

    with connect_sqlite(REGISTRY_DB) as conn:
        row = conn.execute(
            """
            SELECT
                id,
                slug,
                runtime,
                model_name,
                parameters_json,
                system_prompt,
                raw_retention_days,
                raw_max_rows,
                raw_max_mb,
                memory_max_items,
                active
            FROM model_profiles
            WHERE slug = ?
            """,
            (clean_slug,),
        ).fetchone()

    if row is None:
        raise ValueError(f"No existe el perfil de modelo: {clean_slug}")

    return {
        "id": row[0],
        "slug": row[1],
        "runtime": row[2],
        "model_name": row[3],
        "parameters": json.loads(row[4]),
        "system_prompt": row[5],
        "raw_retention_days": row[6],
        "raw_max_rows": row[7],
        "raw_max_mb": row[8],
        "memory_max_items": row[9],
        "active": bool(row[10]),
    }


def list_model_profiles(active_only: bool = True) -> list[dict[str, Any]]:
    init_registry()

    sql = """
        SELECT
            id,
            slug,
            runtime,
            model_name,
            parameters_json,
            system_prompt,
            raw_retention_days,
            raw_max_rows,
            raw_max_mb,
            memory_max_items,
            created_at,
            active
        FROM model_profiles
    """

    if active_only:
        sql += " WHERE active = 1"

    sql += " ORDER BY created_at DESC"

    with connect_sqlite(REGISTRY_DB) as conn:
        rows = conn.execute(sql).fetchall()

    return [
        {
            "id": row[0],
            "slug": row[1],
            "runtime": row[2],
            "model_name": row[3],
            "parameters": json.loads(row[4]),
            "system_prompt": row[5],
            "raw_retention_days": row[6],
            "raw_max_rows": row[7],
            "raw_max_mb": row[8],
            "memory_max_items": row[9],
            "created_at": row[10],
            "active": bool(row[11]),
        }
        for row in rows
    ]


def save_exchange(
    slug: str,
    user_prompt: str,
    request_payload: dict[str, Any],
    model_output: str | None,
    response_payload: dict[str, Any] | None,
    status: str,
    error_text: str | None = None,
) -> dict[str, int]:
    profile = ensure_profile_exists(slug)

    if not profile["active"]:
        raise ValueError(f"Perfil inactivo: {slug}")

    if not user_prompt.strip():
        raise ValueError("user_prompt vacío")

    status_clean = status.strip().lower()

    if status_clean not in {"ok", "error"}:
        raise ValueError("status debe ser 'ok' o 'error'")

    if status_clean == "ok":
        if model_output is None or not model_output.strip():
            raise ValueError("model_output vacío para status='ok'")

    created_at = datetime.now(timezone.utc)
    expires_at = created_at + timedelta(days=int(profile["raw_retention_days"]))

    prompt_hash = sha256_text(user_prompt)
    output_hash = sha256_text(model_output) if model_output is not None else None

    request_json = json.dumps(
        request_payload,
        sort_keys=True,
        ensure_ascii=False,
    )

    response_json = (
        json.dumps(response_payload, sort_keys=True, ensure_ascii=False)
        if response_payload is not None
        else None
    )

    raw_db = get_raw_db_path(profile["slug"])

    with connect_sqlite(raw_db) as conn:
        prompt_cursor = conn.execute(
            """
            INSERT INTO raw_prompts (
                created_at,
                expires_at,
                user_prompt,
                prompt_hash,
                prompt_bytes,
                pinned
            )
            VALUES (?, ?, ?, ?, ?, 0)
            """,
            (
                created_at.isoformat(),
                expires_at.isoformat(),
                user_prompt,
                prompt_hash,
                byte_len(user_prompt),
            ),
        )

        prompt_id = int(prompt_cursor.lastrowid)

        output_cursor = conn.execute(
            """
            INSERT INTO raw_outputs (
                prompt_id,
                created_at,
                model_output,
                output_hash,
                output_bytes,
                request_json,
                response_json,
                status,
                error_text,
                approved_for_memory
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
            """,
            (
                prompt_id,
                created_at.isoformat(),
                model_output,
                output_hash,
                byte_len(model_output),
                request_json,
                response_json,
                status_clean,
                error_text,
            ),
        )

        output_id = int(output_cursor.lastrowid)

    return {
        "prompt_id": prompt_id,
        "output_id": output_id,
    }


def approve_memory(
    slug: str,
    output_id: int,
    saved_text: str,
    reason: str | None = None,
) -> int:
    profile = ensure_profile_exists(slug)

    clean_text = saved_text.strip()

    if not clean_text:
        raise ValueError("saved_text vacío")

    raw_db = get_raw_db_path(profile["slug"])
    memory_db = get_memory_db_path(profile["slug"])

    with connect_sqlite(raw_db) as raw_conn:
        row = raw_conn.execute(
            """
            SELECT id, output_hash, status
            FROM raw_outputs
            WHERE id = ?
            """,
            (output_id,),
        ).fetchone()

    if row is None:
        raise ValueError(f"No existe output_id={output_id} en perfil {profile['slug']}")

    source_output_id = int(row[0])
    source_output_hash = row[1]
    status = row[2]

    if status != "ok":
        raise ValueError("No se puede aprobar memoria desde un output con status!='ok'")

    if not source_output_hash:
        raise ValueError("No se puede aprobar memoria sin source_output_hash")

    saved_text_hash = sha256_text(clean_text)

    try:
        with connect_sqlite(memory_db) as memory_conn:
            cursor = memory_conn.execute(
                """
                INSERT INTO memory_items (
                    created_at,
                    source_output_id,
                    source_output_hash,
                    saved_text,
                    saved_text_hash,
                    reason,
                    active
                )
                VALUES (?, ?, ?, ?, ?, ?, 1)
                """,
                (
                    now_iso(),
                    source_output_id,
                    source_output_hash,
                    clean_text,
                    saved_text_hash,
                    reason,
                ),
            )

            memory_id = int(cursor.lastrowid)

    except sqlite3.IntegrityError as exc:
        raise ValueError("Ese saved_text ya existe en la memoria de este perfil") from exc

    with connect_sqlite(raw_db) as raw_conn:
        raw_conn.execute(
            """
            UPDATE raw_outputs
            SET approved_for_memory = 1
            WHERE id = ?
            """,
            (source_output_id,),
        )

    enforce_memory_limit(profile["slug"])

    return memory_id


def get_memory_context(slug: str, limit: int = 20) -> list[str]:
    profile = ensure_profile_exists(slug)

    if limit <= 0:
        raise ValueError("limit debe ser > 0")

    memory_db = get_memory_db_path(profile["slug"])

    with connect_sqlite(memory_db) as conn:
        rows = conn.execute(
            """
            SELECT saved_text
            FROM memory_items
            WHERE active = 1
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [row[0] for row in rows]


def pin_prompt(slug: str, prompt_id: int, pinned: bool = True) -> None:
    profile = ensure_profile_exists(slug)

    raw_db = get_raw_db_path(profile["slug"])

    with connect_sqlite(raw_db) as conn:
        cursor = conn.execute(
            """
            UPDATE raw_prompts
            SET pinned = ?
            WHERE id = ?
            """,
            (1 if pinned else 0, prompt_id),
        )

        if cursor.rowcount == 0:
            raise ValueError(f"No existe prompt_id={prompt_id}")


def enforce_memory_limit(slug: str) -> int:
    profile = ensure_profile_exists(slug)

    memory_db = get_memory_db_path(profile["slug"])

    with connect_sqlite(memory_db) as conn:
        total_active = conn.execute(
            """
            SELECT COUNT(*)
            FROM memory_items
            WHERE active = 1
            """
        ).fetchone()[0]

        overflow = int(total_active) - int(profile["memory_max_items"])

        if overflow <= 0:
            return 0

        cursor = conn.execute(
            """
            DELETE FROM memory_items
            WHERE id IN (
                SELECT id
                FROM memory_items
                WHERE active = 1
                ORDER BY created_at ASC
                LIMIT ?
            )
            """,
            (overflow,),
        )

        deleted = int(cursor.rowcount)

    compact_db(memory_db)

    return deleted


def prune_raw(slug: str) -> dict[str, int]:
    profile = ensure_profile_exists(slug)

    raw_db = get_raw_db_path(profile["slug"])

    deleted_expired = 0
    deleted_over_rows = 0
    deleted_over_size = 0

    with connect_sqlite(raw_db) as conn:
        cursor = conn.execute(
            """
            DELETE FROM raw_prompts
            WHERE pinned = 0
              AND expires_at < ?
            """,
            (now_iso(),),
        )
        deleted_expired = int(cursor.rowcount)

        total_rows = conn.execute(
            """
            SELECT COUNT(*)
            FROM raw_prompts
            """
        ).fetchone()[0]

        overflow = int(total_rows) - int(profile["raw_max_rows"])

        if overflow > 0:
            cursor = conn.execute(
                """
                DELETE FROM raw_prompts
                WHERE id IN (
                    SELECT id
                    FROM raw_prompts
                    WHERE pinned = 0
                    ORDER BY created_at ASC
                    LIMIT ?
                )
                """,
                (overflow,),
            )
            deleted_over_rows = int(cursor.rowcount)

    compact_db(raw_db)

    max_bytes = int(profile["raw_max_mb"]) * 1024 * 1024

    while db_total_size_bytes(raw_db) > max_bytes:
        with connect_sqlite(raw_db) as conn:
            cursor = conn.execute(
                """
                DELETE FROM raw_prompts
                WHERE id IN (
                    SELECT id
                    FROM raw_prompts
                    WHERE pinned = 0
                    ORDER BY created_at ASC
                    LIMIT 50
                )
                """
            )

            deleted_batch = int(cursor.rowcount)

        if deleted_batch <= 0:
            break

        deleted_over_size += deleted_batch
        compact_db(raw_db)

    return {
        "deleted_expired": deleted_expired,
        "deleted_over_rows": deleted_over_rows,
        "deleted_over_size": deleted_over_size,
    }


def raw_stats(slug: str) -> dict[str, Any]:
    profile = ensure_profile_exists(slug)

    raw_db = get_raw_db_path(profile["slug"])

    with connect_sqlite(raw_db) as conn:
        prompt_count = conn.execute(
            """
            SELECT COUNT(*)
            FROM raw_prompts
            """
        ).fetchone()[0]

        output_row = conn.execute(
            """
            SELECT
                COUNT(*),
                COALESCE(SUM(CASE WHEN status = 'ok' THEN 1 ELSE 0 END), 0),
                COALESCE(SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END), 0),
                COALESCE(SUM(approved_for_memory), 0),
                COALESCE(SUM(output_bytes), 0)
            FROM raw_outputs
            """
        ).fetchone()

    return {
        "slug": profile["slug"],
        "prompt_count": int(prompt_count),
        "output_count": int(output_row[0]),
        "ok_count": int(output_row[1]),
        "error_count": int(output_row[2]),
        "approved_count": int(output_row[3]),
        "output_bytes": int(output_row[4]),
        "db_size_bytes": db_total_size_bytes(raw_db),
        "db_size_mb": round(db_total_size_bytes(raw_db) / 1024 / 1024, 3),
    }


def memory_stats(slug: str) -> dict[str, Any]:
    profile = ensure_profile_exists(slug)

    memory_db = get_memory_db_path(profile["slug"])

    with connect_sqlite(memory_db) as conn:
        row = conn.execute(
            """
            SELECT
                COUNT(*),
                COALESCE(SUM(active), 0)
            FROM memory_items
            """
        ).fetchone()

    return {
        "slug": profile["slug"],
        "items_total": int(row[0]),
        "items_active": int(row[1]),
        "db_size_bytes": db_total_size_bytes(memory_db),
        "db_size_mb": round(db_total_size_bytes(memory_db) / 1024 / 1024, 3),
    }