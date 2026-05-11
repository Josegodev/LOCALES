import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from app.config import settings
from app.services.repo_tools import run_repo_tool_question

REPO_COMMAND = "repo"
REPO_USAGE_TEXT = "Uso: /repo <pregunta>"
REPO_PROMPT_VERSION = "telegram_repo_analyzer_v1"
REPO_PROVIDER = "ollama"
TELEGRAM_SAFE_MESSAGE_CHARS = 3500
TRUNCATED_SUFFIX = "\n\n[respuesta truncada para Telegram]"


class RepoCommandError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


def is_repo_command(text: str) -> bool:
    if not isinstance(text, str):
        return False
    return text == "/repo" or text.startswith("/repo ") or text.startswith("/repo\n")


def parse_repo_command(text: str) -> str:
    if not is_repo_command(text):
        raise RepoCommandError("invalid_repo_usage", REPO_USAGE_TEXT)

    question = text[len("/repo") :].strip()
    if not question:
        raise RepoCommandError("invalid_repo_usage", REPO_USAGE_TEXT)
    return question


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _truncate_for_telegram(text: str, max_chars: int = TELEGRAM_SAFE_MESSAGE_CHARS) -> tuple[str, bool]:
    normalized = text.strip()
    if len(normalized) <= max_chars:
        return normalized, False

    safe_limit = max_chars - len(TRUNCATED_SUFFIX)
    truncated = normalized[:safe_limit].rstrip()
    return f"{truncated}{TRUNCATED_SUFFIX}", True


def _error_result(
    *,
    trace_id: str | None,
    user_id: int | None,
    repo_path: str,
    model: str,
    temperature: float,
    question: str,
    error_code: str,
    error_message: str,
    started_at: float,
    evidence_files: list[str] | None = None,
    warnings: list[str] | None = None,
    reply_text: str | None = None,
) -> dict[str, Any]:
    formatted_reply = reply_text or f"{error_code}: {error_message}"
    safe_reply, truncated = _truncate_for_telegram(formatted_reply)
    return {
        "status": "error",
        "trace_id": trace_id,
        "timestamp": _utc_timestamp(),
        "source": "telegram",
        "command": REPO_COMMAND,
        "user_id": user_id,
        "repo_path": repo_path,
        "provider": REPO_PROVIDER,
        "model": model,
        "temperature": temperature,
        "question": question,
        "evidence_files": evidence_files or [],
        "answer": None,
        "reply_text": safe_reply,
        "error": {
            "error_code": error_code,
            "message": error_message,
            "warnings": warnings or [],
        },
        "error_code": error_code,
        "error_message": error_message,
        "warnings": list(warnings or []) + (["telegram_response_truncated"] if truncated else []),
        "latency_ms": int((time.perf_counter() - started_at) * 1000),
        "truncated": truncated,
    }


def _success_result(
    *,
    trace_id: str | None,
    user_id: int | None,
    repo_path: str,
    model: str,
    temperature: float,
    question: str,
    answer: str,
    evidence_files: list[str],
    started_at: float,
    repo_tool: str,
    requested_file: str | None = None,
    resolved_path: str | None = None,
    start_line: int | None = None,
    end_line: int | None = None,
    query: str | None = None,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    safe_reply, truncated = _truncate_for_telegram(answer)
    normalized_warnings = list(warnings or [])
    if truncated:
        normalized_warnings.append("telegram_response_truncated")
    return {
        "status": "ok",
        "trace_id": trace_id,
        "timestamp": _utc_timestamp(),
        "source": "telegram",
        "command": REPO_COMMAND,
        "repo_tool": repo_tool,
        "user_id": user_id,
        "repo_path": repo_path,
        "provider": REPO_PROVIDER,
        "model": model,
        "temperature": temperature,
        "question": question,
        "evidence_files": evidence_files,
        "answer": answer,
        "reply_text": safe_reply,
        "error": None,
        "error_code": None,
        "error_message": None,
        "warnings": normalized_warnings,
        "requested_file": requested_file,
        "resolved_path": resolved_path,
        "start_line": start_line,
        "end_line": end_line,
        "query": query,
        "latency_ms": int((time.perf_counter() - started_at) * 1000),
        "truncated": truncated,
    }

def _format_find_file_matches(matches: list[str], requested_file: str | None) -> str:
    title = requested_file or "archivo"
    lines = [f"Coincidencias para {title}:"]
    lines.extend(f"- {match}" for match in matches)
    return "\n".join(lines)


def _format_search_matches(matches: list[dict[str, Any]], query: str | None) -> str:
    title = query or ""
    lines = [f"Coincidencias para {title}:"]
    lines.extend(
        f"- {match['path']}:{match['line_number']}: {match['line_excerpt']}"
        for match in matches
    )
    return "\n".join(lines)


def _format_repo_tree(tree: list[str], repo_path: str, warnings: list[str]) -> str:
    header = f"Estructura del repo ({Path(repo_path).name}):"
    lines = [header]
    lines.extend(f"- {entry}" for entry in tree)
    if "tree_truncated" in warnings:
        lines.append("- ...")
    return "\n".join(lines)


def _format_tool_error(tool_result: dict[str, Any]) -> str:
    error = tool_result.get("error") if isinstance(tool_result.get("error"), dict) else {}
    error_code = str(error.get("error_code") or "UNKNOWN_ERROR")
    message = str(error.get("message") or "Error desconocido.")
    lines = [f"Error repo_analyzer:\n{error_code} - {message}"]

    matches = tool_result.get("matches")
    if error_code == "AMBIGUOUS_FILE_MATCH" and isinstance(matches, list):
        lines.extend(f"- {match}" for match in matches if isinstance(match, str))

    return "\n".join(lines)


def _tool_result_to_service_result(
    *,
    tool_result: dict[str, Any],
    trace_id: str | None,
    user_id: int | None,
    repo_path: str,
    model: str,
    temperature: float,
    question: str,
    started_at: float,
) -> dict[str, Any]:
    repo_tool = str(tool_result.get("repo_tool") or "ask_repo_llm")
    warnings = tool_result.get("warnings")
    if not isinstance(warnings, list) or not all(isinstance(item, str) for item in warnings):
        warnings = []

    if tool_result.get("status") != "ok":
        error = tool_result.get("error") if isinstance(tool_result.get("error"), dict) else {}
        return _error_result(
            trace_id=trace_id,
            user_id=user_id,
            repo_path=repo_path,
            model=model,
            temperature=temperature,
            question=question,
            error_code=str(error.get("error_code") or "UNKNOWN_ERROR"),
            error_message=str(error.get("message") or "Error desconocido."),
            evidence_files=tool_result.get("evidence_files") if isinstance(tool_result.get("evidence_files"), list) else [],
            warnings=warnings,
            reply_text=_format_tool_error(tool_result),
            started_at=started_at,
        ) | {
            "repo_tool": repo_tool,
            "requested_file": tool_result.get("requested_file"),
            "resolved_path": tool_result.get("resolved_path"),
            "start_line": tool_result.get("start_line"),
            "end_line": tool_result.get("end_line"),
            "query": tool_result.get("query"),
        }

    if repo_tool == "read_file_range":
        resolved_path = str(tool_result.get("resolved_path") or tool_result.get("requested_file") or "")
        start_line = int(tool_result.get("start_line"))
        end_line = int(tool_result.get("end_line"))
        lines = tool_result.get("lines") if isinstance(tool_result.get("lines"), list) else []
        answer = f"{resolved_path} líneas {start_line}-{end_line}:\n" + "\n".join(lines)
        return _success_result(
            trace_id=trace_id,
            user_id=user_id,
            repo_path=repo_path,
            model=model,
            temperature=temperature,
            question=question,
            answer=answer,
            evidence_files=[resolved_path] if resolved_path else [],
            started_at=started_at,
            repo_tool=repo_tool,
            requested_file=tool_result.get("requested_file"),
            resolved_path=resolved_path,
            start_line=start_line,
            end_line=end_line,
            warnings=warnings,
        )

    if repo_tool == "find_file":
        matches = tool_result.get("matches") if isinstance(tool_result.get("matches"), list) else []
        answer = _format_find_file_matches(matches, tool_result.get("requested_file"))
        return _success_result(
            trace_id=trace_id,
            user_id=user_id,
            repo_path=repo_path,
            model=model,
            temperature=temperature,
            question=question,
            answer=answer,
            evidence_files=[match for match in matches if isinstance(match, str)],
            started_at=started_at,
            repo_tool=repo_tool,
            requested_file=tool_result.get("requested_file"),
            resolved_path=tool_result.get("resolved_path"),
            warnings=warnings,
        )

    if repo_tool == "search_text":
        matches = tool_result.get("matches") if isinstance(tool_result.get("matches"), list) else []
        answer = _format_search_matches(matches, tool_result.get("query"))
        evidence_files = [
            match["path"]
            for match in matches
            if isinstance(match, dict) and isinstance(match.get("path"), str)
        ]
        return _success_result(
            trace_id=trace_id,
            user_id=user_id,
            repo_path=repo_path,
            model=model,
            temperature=temperature,
            question=question,
            answer=answer,
            evidence_files=evidence_files,
            started_at=started_at,
            repo_tool=repo_tool,
            query=tool_result.get("query"),
            warnings=warnings,
        )

    if repo_tool == "repo_tree":
        tree = tool_result.get("tree") if isinstance(tool_result.get("tree"), list) else []
        answer = _format_repo_tree(tree, repo_path, warnings)
        return _success_result(
            trace_id=trace_id,
            user_id=user_id,
            repo_path=repo_path,
            model=model,
            temperature=temperature,
            question=question,
            answer=answer,
            evidence_files=[],
            started_at=started_at,
            repo_tool=repo_tool,
            warnings=warnings,
        )

    answer = str(tool_result.get("answer") or "")
    evidence_files = tool_result.get("evidence_files")
    if not isinstance(evidence_files, list) or not all(isinstance(item, str) for item in evidence_files):
        evidence_files = []
    return _success_result(
        trace_id=trace_id,
        user_id=user_id,
        repo_path=repo_path,
        model=model,
        temperature=temperature,
        question=question,
        answer=answer,
        evidence_files=evidence_files,
        started_at=started_at,
        repo_tool=repo_tool,
        warnings=warnings,
    )


def build_repo_trace_metadata(result: dict[str, Any]) -> dict[str, Any]:
    evidence_files = result.get("evidence_files")
    if not isinstance(evidence_files, list) or not all(isinstance(item, str) for item in evidence_files):
        evidence_files = []

    warnings = result.get("warnings")
    if not isinstance(warnings, list) or not all(isinstance(item, str) for item in warnings):
        warnings = []

    return {
        "provider": result.get("provider"),
        "temperature": result.get("temperature"),
        "prompt_version": REPO_PROMPT_VERSION,
        "repo_tool": result.get("repo_tool"),
        "repo_path": result.get("repo_path"),
        "question": result.get("question"),
        "requested_file": result.get("requested_file"),
        "resolved_path": result.get("resolved_path"),
        "start_line": result.get("start_line"),
        "end_line": result.get("end_line"),
        "query": result.get("query"),
        "evidence_files": evidence_files,
        "source_filenames": evidence_files,
        "warnings": warnings,
    }


def run_repo_analysis_question(
    question: str,
    user_id: int | None = None,
    *,
    trace_id: str | None = None,
    session_factory: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    started_at = time.perf_counter()
    repo_path = settings.repo_analyzer_path.strip()
    model = settings.repo_analyzer_model.strip()
    temperature = float(settings.repo_analyzer_temperature)
    normalized_question = question.strip()

    if not settings.repo_analyzer_enabled:
        return _error_result(
            trace_id=trace_id,
            user_id=user_id,
            repo_path=repo_path,
            model=model,
            temperature=temperature,
            question=normalized_question,
            error_code="REPO_ANALYZER_DISABLED",
            error_message="repo_analyzer no está habilitado.",
            reply_text="repo_analyzer no está habilitado.",
            started_at=started_at,
        )

    if not normalized_question:
        return _error_result(
            trace_id=trace_id,
            user_id=user_id,
            repo_path=repo_path,
            model=model,
            temperature=temperature,
            question=normalized_question,
            error_code="invalid_repo_usage",
            error_message=REPO_USAGE_TEXT,
            reply_text=REPO_USAGE_TEXT,
            started_at=started_at,
        )

    if not repo_path or not Path(repo_path).is_dir():
        return _error_result(
            trace_id=trace_id,
            user_id=user_id,
            repo_path=repo_path,
            model=model,
            temperature=temperature,
            question=normalized_question,
            error_code="INVALID_REPO_PATH",
            error_message="REPO_ANALYZER_PATH no es un directorio válido.",
            started_at=started_at,
        )

    try:
        tool_result = run_repo_tool_question(
            repo_path,
            normalized_question,
            model,
            temperature,
            session_factory=session_factory,
        )
    except Exception as exc:
        return _error_result(
            trace_id=trace_id,
            user_id=user_id,
            repo_path=repo_path,
            model=model,
            temperature=temperature,
            question=normalized_question,
            error_code="REPO_TOOL_ROUTER_FAILED",
            error_message=exc.__class__.__name__,
            started_at=started_at,
        )

    return _tool_result_to_service_result(
        tool_result=tool_result,
        trace_id=trace_id,
        user_id=user_id,
        repo_path=repo_path,
        model=model,
        temperature=temperature,
        question=normalized_question,
        started_at=started_at,
    )


def handle_repo_command(
    text: str,
    user_id: int | None = None,
    *,
    trace_id: str | None = None,
    session_factory: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    try:
        question = parse_repo_command(text)
    except RepoCommandError as exc:
        return _error_result(
            trace_id=trace_id,
            user_id=user_id,
            repo_path=settings.repo_analyzer_path.strip(),
            model=settings.repo_analyzer_model.strip(),
            temperature=float(settings.repo_analyzer_temperature),
            question="",
            error_code=exc.code,
            error_message=exc.message,
            reply_text=exc.message,
            started_at=time.perf_counter(),
        )

    return run_repo_analysis_question(
        question,
        user_id=user_id,
        trace_id=trace_id,
        session_factory=session_factory,
    )
