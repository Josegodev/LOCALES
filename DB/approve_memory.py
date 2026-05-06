import argparse
from pathlib import Path

from db_store import approve_memory


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument("--slug", required=True)
    parser.add_argument("--output-id", type=int, required=True)
    parser.add_argument("--text", default=None)
    parser.add_argument("--file", default=None)
    parser.add_argument("--reason", default=None)

    args = parser.parse_args()

    if args.text and args.file:
        raise SystemExit("Usa --text o --file, no ambos")

    if args.file:
        saved_text = Path(args.file).read_text(encoding="utf-8")
    elif args.text:
        saved_text = args.text
    else:
        raise SystemExit("Falta --text o --file")

    memory_id = approve_memory(
        slug=args.slug,
        output_id=args.output_id,
        saved_text=saved_text,
        reason=args.reason,
    )

    print(f"memory_id={memory_id}")


if __name__ == "__main__":
    main()