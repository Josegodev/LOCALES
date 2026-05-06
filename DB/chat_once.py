import argparse
import sys
from typing import Any

from db_store import (
    ensure_profile_exists,
    get_memory_context,
    save_exchange,
)
from lmstudio_client import (
    extract_message_content,
    load_config,
    send_chat_completion,
)


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


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument("--slug", required=True)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--memory-limit", type=int, default=None)

    args = parser.parse_args()

    profile = ensure_profile_exists(args.slug)

    if not profile["active"]:
        raise SystemExit(f"Perfil inactivo: {args.slug}")

    config = load_config()

    memory_limit = (
        args.memory_limit
        if args.memory_limit is not None
        else int(config.get("default_memory_limit", 20))
    )

    approved_memory = get_memory_context(
        slug=profile["slug"],
        limit=memory_limit,
    )

    messages = build_messages(
        system_prompt=profile["system_prompt"],
        approved_memory=approved_memory,
        user_prompt=args.prompt,
    )

    payload = build_payload(
        model_name=profile["model_name"],
        parameters=profile["parameters"],
        messages=messages,
    )

    try:
        response_json = send_chat_completion(payload)
        model_output = extract_message_content(response_json)

        ids = save_exchange(
            slug=profile["slug"],
            user_prompt=args.prompt,
            request_payload=payload,
            model_output=model_output,
            response_payload=response_json,
            status="ok",
            error_text=None,
        )

        print(f"prompt_id={ids['prompt_id']}")
        print(f"output_id={ids['output_id']}")
        print("")
        print(model_output)

    except Exception as exc:
        ids = save_exchange(
            slug=profile["slug"],
            user_prompt=args.prompt,
            request_payload=payload,
            model_output=None,
            response_payload=None,
            status="error",
            error_text=str(exc),
        )

        print(f"prompt_id={ids['prompt_id']}", file=sys.stderr)
        print(f"output_id={ids['output_id']}", file=sys.stderr)
        print(f"error={exc}", file=sys.stderr)

        raise SystemExit(1)


if __name__ == "__main__":
    main()