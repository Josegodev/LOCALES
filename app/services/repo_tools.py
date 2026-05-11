from __future__ import annotations

import os
import re
import sys
from importlib import import_module
from pathlib import Path
from typing import Any, Callable

MAX_FILE_SIZE_BYTES = 200 * 1024
DEFAULT_TREE_MAX_FILES = 200
DEFAULT_SEARCH_LIMIT = 20
DEFAULT_ANALYZER_APP_DIR = Path(__file__).resolve().parents[3] / "Analyzer" / "app"

EXCLUDED_DIR_NAMES = {
    ".cache",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
}

EXCLUDED_FILE_SUFFIXES = {
    ".7z",
    ".avi",
    ".bin",
    ".bmp",
    ".class",
    ".db",
    ".dll",
    ".dylib",
    ".env",
    ".exe",
    ".gif",
    ".gz",
    ".ico",
    ".jar",
    ".jpeg",
    ".jpg",
    ".mov",
    ".mp3",
    ".mp4",
    ".o",
    ".otf",
    ".pdf",
    ".png",
    ".pyc",
    ".pyd",
    ".pyo",
    ".so",
    ".sqlite",
    ".sqlite3",
    ".svg",
    ".svgz",
    ".tar",
    ".ttf",
    ".wav",
    ".webm",
    ".webp",
    ".zip",
}


class RepoToolsError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


class RepoAnalyzerImportError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


def normalize_repo_path(repo_path: str) -> Path:
    root = Path(repo_path).expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(f"Repository path does not exist: {repo_path}")
    if not root.is_dir():
        raise NotADirectoryError(f"Repository path is not a directory: {repo_path}")
    return root


def should_skip_dir(dir_name: str) -> bool:
    return dir_name in EXCLUDED_DIR_NAMES


def is_env_file(path: Path) -> bool:
    return path.name == ".env" or path.name.startswith(".env.")


def is_binary_file(path: Path) -> bool:
    try:
        with path.open("rb") as handle:
            sample = handle.read(1024)
    except OSError:
        return True
    return b"\x00" in sample


def should_skip_file(path: Path) -> bool:
    if is_env_file(path):
        return True
    if path.suffix.lower() in EXCLUDED_FILE_SUFFIXES:
        return True
    try:
        if path.stat().st_size > MAX_FILE_SIZE_BYTES:
            return True
    except OSError:
        return True
    return is_binary_file(path)


def iter_repo_files(repo_path: str):
    root = normalize_repo_path(repo_path)
    for current_root, dir_names, file_names in os.walk(root):
        dir_names[:] = sorted(name for name in dir_names if not should_skip_dir(name))
        for file_name in sorted(file_names):
            candidate = Path(current_root, file_name)
            if should_skip_file(candidate):
                continue
            yield candidate


def to_relative_path(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _build_error(
    repo_tool: str,
    error_code: str,
    message: str,
    **fields: Any,
) -> dict[str, Any]:
    return {
        "status": "error",
        "repo_tool": repo_tool,
        "error": {
            "error_code": error_code,
            "message": message,
            "warnings": fields.pop("warnings", []),
        },
        **fields,
    }


def _normalize_requested_path(value: str) -> str:
    normalized = value.strip().replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def _validate_requested_path(value: str) -> str:
    normalized = _normalize_requested_path(value)
    if not normalized:
        raise RepoToolsError("INVALID_FILE_PATH", "Debe indicar un archivo válido.")
    candidate = Path(normalized)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise RepoToolsError("INVALID_FILE_PATH", "No se permiten rutas fuera del repositorio.")
    return normalized


def repo_tree(repo_path: str, max_files: int = DEFAULT_TREE_MAX_FILES) -> dict[str, Any]:
    root = normalize_repo_path(repo_path)
    tree: list[str] = []
    warnings: list[str] = []

    for index, path in enumerate(iter_repo_files(str(root)), start=1):
        if index > max_files:
            warnings.append("tree_truncated")
            break
        tree.append(to_relative_path(root, path))

    return {
        "status": "ok",
        "repo_tool": "repo_tree",
        "root": str(root),
        "tree": tree,
        "warnings": warnings,
    }


def find_file(repo_path: str, filename_or_path: str) -> dict[str, Any]:
    root = normalize_repo_path(repo_path)
    requested_file = _validate_requested_path(filename_or_path)
    search_value = requested_file.casefold()
    exact_path_requested = "/" in requested_file
    matches: list[str] = []

    for path in iter_repo_files(str(root)):
        relative_path = to_relative_path(root, path)
        if exact_path_requested:
            if relative_path.casefold() == search_value:
                matches.append(relative_path)
                break
            continue

        if path.name.casefold() == search_value:
            matches.append(relative_path)

    if not matches:
        return _build_error(
            "find_file",
            "FILE_NOT_FOUND",
            f"No se encontró el archivo: {requested_file}",
            requested_file=requested_file,
            matches=[],
        )

    if len(matches) > 1:
        return _build_error(
            "find_file",
            "AMBIGUOUS_FILE_MATCH",
            f"Hay varias coincidencias para: {requested_file}",
            requested_file=requested_file,
            matches=matches,
        )

    return {
        "status": "ok",
        "repo_tool": "find_file",
        "root": str(root),
        "requested_file": requested_file,
        "matches": matches,
        "resolved_path": matches[0],
        "warnings": [],
    }


def read_file_range(
    repo_path: str,
    filename_or_path: str,
    start_line: int,
    end_line: int | None = None,
) -> dict[str, Any]:
    if start_line <= 0:
        return _build_error(
            "read_file_range",
            "LINE_OUT_OF_RANGE",
            "Las líneas deben empezar en 1.",
            requested_file=filename_or_path,
            start_line=start_line,
            end_line=end_line,
        )

    resolved = find_file(repo_path, filename_or_path)
    if resolved.get("status") != "ok":
        return {
            **resolved,
            "repo_tool": "read_file_range",
            "start_line": start_line,
            "end_line": end_line,
        }

    root = normalize_repo_path(repo_path)
    resolved_path = str(resolved["resolved_path"])
    absolute_path = (root / resolved_path).resolve()

    if end_line is None:
        end_line = start_line
    if end_line < start_line:
        return _build_error(
            "read_file_range",
            "LINE_OUT_OF_RANGE",
            "El rango de líneas es inválido.",
            requested_file=resolved["requested_file"],
            resolved_path=resolved_path,
            start_line=start_line,
            end_line=end_line,
        )

    try:
        with absolute_path.open("r", encoding="utf-8", errors="replace") as handle:
            file_lines = handle.readlines()
    except OSError:
        return _build_error(
            "read_file_range",
            "FILE_READ_ERROR",
            f"No se pudo leer el archivo: {resolved_path}",
            requested_file=resolved["requested_file"],
            resolved_path=resolved_path,
            start_line=start_line,
            end_line=end_line,
        )

    total_lines = len(file_lines)
    if start_line > total_lines or end_line > total_lines:
        return _build_error(
            "read_file_range",
            "LINE_OUT_OF_RANGE",
            f"El archivo tiene {total_lines} líneas.",
            requested_file=resolved["requested_file"],
            resolved_path=resolved_path,
            start_line=start_line,
            end_line=end_line,
        )

    numbered_lines = [
        f"{line_number}: {file_lines[line_number - 1].rstrip()}"
        for line_number in range(start_line, end_line + 1)
    ]

    return {
        "status": "ok",
        "repo_tool": "read_file_range",
        "root": str(root),
        "requested_file": resolved["requested_file"],
        "resolved_path": resolved_path,
        "start_line": start_line,
        "end_line": end_line,
        "lines": numbered_lines,
        "warnings": [],
    }


def search_text(repo_path: str, query: str, limit: int = DEFAULT_SEARCH_LIMIT) -> dict[str, Any]:
    root = normalize_repo_path(repo_path)
    normalized_query = query.strip()
    if not normalized_query:
        return _build_error(
            "search_text",
            "EMPTY_QUERY",
            "La búsqueda no puede estar vacía.",
            query=query,
            matches=[],
        )

    matches: list[dict[str, Any]] = []
    lowered_query = normalized_query.casefold()

    for path in iter_repo_files(str(root)):
        try:
            with path.open("r", encoding="utf-8", errors="replace") as handle:
                for line_number, line in enumerate(handle, start=1):
                    if lowered_query not in line.casefold():
                        continue
                    matches.append(
                        {
                            "path": to_relative_path(root, path),
                            "line_number": line_number,
                            "line_excerpt": line.rstrip()[:240],
                        }
                    )
                    if len(matches) >= limit:
                        return {
                            "status": "ok",
                            "repo_tool": "search_text",
                            "root": str(root),
                            "query": normalized_query,
                            "matches": matches,
                            "warnings": ["search_truncated"],
                        }
        except OSError:
            continue

    return {
        "status": "ok",
        "repo_tool": "search_text",
        "root": str(root),
        "query": normalized_query,
        "matches": matches,
        "warnings": [],
    }


def _load_repo_chat_session_class():
    analyzer_app_dir = DEFAULT_ANALYZER_APP_DIR
    analyzer_app_dir_str = str(analyzer_app_dir)
    if analyzer_app_dir.is_dir() and analyzer_app_dir_str not in sys.path:
        sys.path.append(analyzer_app_dir_str)

    try:
        module = import_module("repo_analyzer.repo_chat")
    except ModuleNotFoundError as exc:
        raise RepoAnalyzerImportError(
            "REPO_ANALYZER_UNAVAILABLE",
            "repo_analyzer no está disponible.",
        ) from exc
    except Exception as exc:
        raise RepoAnalyzerImportError(
            "REPO_ANALYZER_UNAVAILABLE",
            f"repo_analyzer no se pudo cargar: {exc.__class__.__name__}",
        ) from exc

    session_class = getattr(module, "RepoChatSession", None)
    if session_class is None:
        raise RepoAnalyzerImportError(
            "REPO_ANALYZER_UNAVAILABLE",
            "repo_analyzer no expone RepoChatSession.",
        )
    return session_class


def ask_repo_llm(
    repo_path: str,
    question: str,
    model: str,
    temperature: float,
    *,
    session_factory: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    try:
        factory = session_factory or _load_repo_chat_session_class()
        session = factory(
            repo_path=repo_path,
            model=model,
            temperature=temperature,
        )
    except RepoAnalyzerImportError as exc:
        return _build_error(
            "ask_repo_llm",
            exc.code,
            exc.message,
            repo_path=repo_path,
            model=model,
            temperature=temperature,
            question=question,
            evidence_files=[],
        )
    except ValueError as exc:
        return _build_error(
            "ask_repo_llm",
            "INVALID_REPO_PATH",
            str(exc),
            repo_path=repo_path,
            model=model,
            temperature=temperature,
            question=question,
            evidence_files=[],
        )
    except Exception as exc:
        return _build_error(
            "ask_repo_llm",
            "REPO_ANALYZER_UNAVAILABLE",
            exc.__class__.__name__,
            repo_path=repo_path,
            model=model,
            temperature=temperature,
            question=question,
            evidence_files=[],
        )

    try:
        result = session.ask(question.strip())
    except Exception as exc:
        return _build_error(
            "ask_repo_llm",
            "REPO_ANALYZER_UNAVAILABLE",
            exc.__class__.__name__,
            repo_path=repo_path,
            model=model,
            temperature=temperature,
            question=question,
            evidence_files=[],
        )

    result = dict(result)
    result["repo_tool"] = "ask_repo_llm"
    return result


def _match_single_line(question: str) -> tuple[int, int, str] | None:
    patterns = (
        r"^\s*(?:cual\s+es\s+)?(?:la\s+)?l[íi]nea\s+(\d+)\s+(?:de|del|of)\s+(.+?)\s*$",
        r"^\s*line\s+(\d+)\s+of\s+(.+?)\s*$",
    )
    for pattern in patterns:
        match = re.match(pattern, question, flags=re.IGNORECASE)
        if match:
            line_number = int(match.group(1))
            return line_number, line_number, match.group(2).strip()
    return None


def _match_line_range(question: str) -> tuple[int, int, str] | None:
    patterns = (
        r"^\s*l[íi]neas?\s+(\d+)\s*(?:-|a)\s*(\d+)\s+(?:de|del|of)\s+(.+?)\s*$",
        r"^\s*lines?\s+(\d+)\s*(?:-|to)\s*(\d+)\s+of\s+(.+?)\s*$",
    )
    for pattern in patterns:
        match = re.match(pattern, question, flags=re.IGNORECASE)
        if match:
            start_line = int(match.group(1))
            end_line = int(match.group(2))
            return start_line, end_line, match.group(3).strip()
    return None


def _match_search_text(question: str) -> str | None:
    patterns = (
        r"^\s*busca\s+(.+?)\s*$",
        r"^\s*buscar\s+(.+?)\s*$",
        r"^\s*search\s+(.+?)\s*$",
    )
    for pattern in patterns:
        match = re.match(pattern, question, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def _match_find_file(question: str) -> str | None:
    patterns = (
        r"^\s*d[óo]nde\s+est[aá]\s+(.+?)\s*$",
        r"^\s*where\s+is\s+(.+?)\s*$",
    )
    for pattern in patterns:
        match = re.match(pattern, question, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def _is_repo_tree_question(question: str) -> bool:
    normalized = question.strip().casefold()
    return normalized in {
        "estructura del repo",
        "estructura de repo",
        "arbol del repo",
        "árbol del repo",
        "repo tree",
        "tree of repo",
    }


def route_repo_question(question: str) -> dict[str, Any]:
    matched_range = _match_line_range(question)
    if matched_range is not None:
        start_line, end_line, requested_file = matched_range
        return {
            "repo_tool": "read_file_range",
            "requested_file": requested_file,
            "start_line": start_line,
            "end_line": end_line,
        }

    matched_single = _match_single_line(question)
    if matched_single is not None:
        start_line, end_line, requested_file = matched_single
        return {
            "repo_tool": "read_file_range",
            "requested_file": requested_file,
            "start_line": start_line,
            "end_line": end_line,
        }

    query = _match_search_text(question)
    if query is not None:
        return {
            "repo_tool": "search_text",
            "query": query,
        }

    requested_file = _match_find_file(question)
    if requested_file is not None:
        return {
            "repo_tool": "find_file",
            "requested_file": requested_file,
        }

    if _is_repo_tree_question(question):
        return {
            "repo_tool": "repo_tree",
        }

    return {
        "repo_tool": "ask_repo_llm",
    }


def run_repo_tool_question(
    repo_path: str,
    question: str,
    model: str,
    temperature: float,
    *,
    session_factory: Callable[..., Any] | None = None,
    ask_repo_llm_fn: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
    route = route_repo_question(question)
    repo_tool = route["repo_tool"]

    if repo_tool == "read_file_range":
        return read_file_range(
            repo_path,
            route["requested_file"],
            route["start_line"],
            route["end_line"],
        )

    if repo_tool == "search_text":
        return search_text(repo_path, route["query"])

    if repo_tool == "find_file":
        return find_file(repo_path, route["requested_file"])

    if repo_tool == "repo_tree":
        return repo_tree(repo_path)

    llm_runner = ask_repo_llm_fn or ask_repo_llm
    return llm_runner(
        repo_path,
        question,
        model,
        temperature,
        session_factory=session_factory,
    )
