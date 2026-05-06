import argparse
from db_store import prune_raw, raw_stats, memory_stats


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument("--slug", required=True)
    parser.add_argument("--stats", action="store_true")

    args = parser.parse_args()

    if args.stats:
        print("RAW:")
        print(raw_stats(args.slug))
        print("")
        print("MEMORY:")
        print(memory_stats(args.slug))
        return

    result = prune_raw(args.slug)
    print(result)


if __name__ == "__main__":
    main()