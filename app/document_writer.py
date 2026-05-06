import json
import time
from datetime import datetime, timezone
from pathlib import Path

SAFE_ROOT = Path.home() / "LOCALES" / "TELEGRAM_DOCS"
BASE_DIR = SAFE_ROOT
ALLOWED_EXTENSIONS = {".md"}
MAX_CONTENT_CHARS = 100_000


class DocumentWriteError(Exception):
    def __init__(self, code: str, detail: str):
        self.code = code
        self.detail = detail
        super().__init__(detail)


def create_document(
    filename: str,
    content: str,
    *,
    request_id: str,
    overwrite: bool = False,
) -> dict:
    started_at = time.perf_counter()
    logged_filename = filename if isinstance(filename, str) else ""
    status = "error"
    reason = "unexpected_error"
    output_path = ""

    try:
        if not filename or not isinstance(filename, str):
            raise DocumentWriteError("filename_required", "filename requerido")

        filename = filename.strip()
        logged_filename = filename

        if not filename:
            raise DocumentWriteError("filename_required", "filename requerido")

        if Path(filename).is_absolute():
            raise DocumentWriteError("absolute_path_not_allowed", "no se permiten rutas absolutas")

        if ".." in filename:
            raise DocumentWriteError("parent_directory_not_allowed", "no se permite '..'")

        if "/" in filename or "\\" in filename:
            raise DocumentWriteError("path_not_allowed", "no se permiten rutas")

        if Path(filename).suffix.lower() not in ALLOWED_EXTENSIONS:
            raise DocumentWriteError("extension_not_allowed", "solo se permiten archivos .md")

        if not isinstance(content, str):
            raise DocumentWriteError("content_invalid", "content debe ser texto")

        if not content.strip():
            raise DocumentWriteError("content_required", "content requerido")

        if len(content) > MAX_CONTENT_CHARS:
            raise DocumentWriteError("content_too_large", "contenido demasiado grande")

        SAFE_ROOT.mkdir(parents=True, exist_ok=True)

        base = SAFE_ROOT.resolve()
        target = (base / filename).resolve()

        try:
            target.relative_to(base)
        except ValueError:
            raise DocumentWriteError("path_traversal_blocked", "fuera del directorio permitido")

        if target.exists() and not overwrite:
            raise DocumentWriteError("file_exists", "el archivo ya existe")

        mode = "w" if overwrite else "x"
        with target.open(mode, encoding="utf-8") as f:
            f.write(content)

        output_path = str(target)
        status = "created"
        reason = "created"
        return {
            "request_id": request_id,
            "status": "created",
            "filename": target.name,
            "path": output_path,
            "chars": len(content),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    except DocumentWriteError as exc:
        status = "rejected"
        reason = exc.code
        raise
    except Exception as exc:
        reason = exc.__class__.__name__
        raise
    finally:
        event = {
            "component": "document_writer",
            "request_id": request_id,
            "filename": logged_filename,
            "status": status,
            "reason": reason,
            "duration_ms": int((time.perf_counter() - started_at) * 1000),
        }
        if output_path:
            event["path"] = output_path
        print(json.dumps(event, ensure_ascii=False, sort_keys=True), flush=True)
