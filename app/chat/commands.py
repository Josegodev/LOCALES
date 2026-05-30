from __future__ import annotations

CREATE_DOCUMENT_COMMAND = "creardoc"
CREATE_DOCUMENT_PREFIX = "/creardoc"


def parse_chat_command(message: str) -> dict[str, str] | None:
    if not isinstance(message, str):
        return None

    stripped_message = message.strip()
    if not stripped_message:
        return None

    if not stripped_message.casefold().startswith(CREATE_DOCUMENT_PREFIX):
        return None

    instruction = stripped_message[len(CREATE_DOCUMENT_PREFIX):].strip()
    return {
        "command": CREATE_DOCUMENT_COMMAND,
        "instruction": instruction,
    }
