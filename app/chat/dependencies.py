from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from app.config import Settings


@dataclass(slots=True)
class ChatDependencies:
    ask_chat: Callable[..., dict[str, Any]]
    build_document_prompt: Callable[..., dict[str, Any]]
    query_remote_rag: Callable[..., dict[str, Any]]
    resolve_provider_model: Callable[..., tuple[str, str]]
    save_chat_run: Callable[[dict[str, Any]], None]
    log_event: Callable[..., None]
    new_trace_id: Callable[[], str]
    settings: Settings
    create_document_tool: Callable[..., Any] | None = None
