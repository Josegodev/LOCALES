from datetime import datetime
from pathlib import Path
import re


DOCUMENTS_DIR = Path("outputs/documents")
MAX_DOCUMENT_CHARS = 20_000
DEFAULT_DOCUMENT_BASENAME = "documento"
TRACE_ID_FALLBACK = "no_trace"


def slugify(text: str, max_len: int = 50) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9áéíóúñü]+", "_", text)
    text = text.strip("_")
    return text[:max_len] or DEFAULT_DOCUMENT_BASENAME


def _normalize_document_name(*, filename: str | None = None, title: str | None = None) -> str:
    candidate = ""

    if isinstance(filename, str):
        candidate = filename.strip()
    if not candidate and isinstance(title, str):
        candidate = title.strip()
    if not candidate:
        return DEFAULT_DOCUMENT_BASENAME

    candidate_path = Path(candidate)
    if candidate_path.is_absolute():
        return DEFAULT_DOCUMENT_BASENAME
    if candidate_path.name != candidate:
        return DEFAULT_DOCUMENT_BASENAME
    if ".." in candidate:
        return DEFAULT_DOCUMENT_BASENAME

    if candidate_path.suffix:
        if candidate_path.suffix.lower() != ".md":
            return DEFAULT_DOCUMENT_BASENAME
        candidate = candidate_path.stem

    return slugify(candidate)


def _normalize_trace_fragment(trace_id: str) -> str:
    normalized = trace_id.strip() if isinstance(trace_id, str) else ""
    if not normalized:
        return TRACE_ID_FALLBACK
    return slugify(normalized, max_len=8)


def write_document(
    *,
    content: str,
    trace_id: str,
    filename: str | None = None,
    title: str | None = None,
) -> dict:
    DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)

    if not content.strip():
        return {
            "status": "error",
            "error_type": "empty_document",
            "error_message": "El modelo no generó contenido.",
        }

    if len(content) > MAX_DOCUMENT_CHARS:
        content = content[:MAX_DOCUMENT_CHARS]

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_name = _normalize_document_name(filename=filename, title=title)
    trace_fragment = _normalize_trace_fragment(trace_id)
    filename = f"{timestamp}_{safe_name}_{trace_fragment}.md"

    path = DOCUMENTS_DIR / filename

    path.write_text(content, encoding="utf-8")

    return {
        "status": "ok",
        "document_path": str(path),
        "document_filename": filename,
        "chars_written": len(content),
    }
