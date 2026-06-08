from typing import Any


def build_messages(
    system_prompt: str,
    approved_memory: list[str],
    user_prompt: str,
) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []

    system_parts: list[str] = []

    if system_prompt.strip():
        system_parts.append(system_prompt.strip())

    if approved_memory:
        memory_block = "\n".join(f"- {item}" for item in approved_memory)

        system_parts.append(
            "Memoria aprobada del perfil actual. "
            "Usa esta información solo si es relevante:\n"
            f"{memory_block}"
        )

    if system_parts:
        messages.append(
            {
                "role": "system",
                "content": "\n\n".join(system_parts),
            }
        )

    messages.append(
        {
            "role": "user",
            "content": user_prompt,
        }
    )

    return messages


def build_payload(
    model_name: str,
    parameters: dict[str, Any],
    messages: list[dict[str, str]],
) -> dict[str, Any]:
    payload = {
        "model": model_name,
        "messages": messages,
    }

    payload.update(parameters)
    payload["stream"] = False

    return payload
