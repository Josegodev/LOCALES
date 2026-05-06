import argparse
from db_store import create_model_profile


DEFAULT_SYSTEM_PROMPT = (
    "Responde de forma técnica, directa y verificable. "
    "No afirmes que algo se ha guardado en memoria. "
    "La memoria persistente la controla un sistema externo."
)


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument("--slug", required=True)
    parser.add_argument("--model-name", required=True)

    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--top-p", type=float, default=None)
    parser.add_argument("--max-tokens", type=int, default=None)

    parser.add_argument("--system-prompt", default=DEFAULT_SYSTEM_PROMPT)

    parser.add_argument("--raw-retention-days", type=int, default=14)
    parser.add_argument("--raw-max-rows", type=int, default=500)
    parser.add_argument("--raw-max-mb", type=int, default=200)
    parser.add_argument("--memory-max-items", type=int, default=200)

    args = parser.parse_args()

    parameters = {
        "temperature": args.temperature,
        "stream": False,
    }

    if args.top_p is not None:
        parameters["top_p"] = args.top_p

    if args.max_tokens is not None:
        parameters["max_tokens"] = args.max_tokens

    profile_id = create_model_profile(
        slug=args.slug,
        runtime="lmstudio",
        model_name=args.model_name,
        parameters=parameters,
        system_prompt=args.system_prompt,
        raw_retention_days=args.raw_retention_days,
        raw_max_rows=args.raw_max_rows,
        raw_max_mb=args.raw_max_mb,
        memory_max_items=args.memory_max_items,
    )

    print(f"Perfil creado: id={profile_id}, slug={args.slug}")


if __name__ == "__main__":
    main()