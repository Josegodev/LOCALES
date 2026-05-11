from __future__ import annotations

import argparse

from document_context import build_document_prompt
from lmstudio_client import ask_lmstudio


def ask_once(
    query: str,
    top_k: int,
    allowed_source_filenames: list[str] | None = None,
    retrieval_only: bool = False,
) -> None:
    query = query.strip()

    if not query:
        print("ERROR: pregunta vacía")
        return

    context = build_document_prompt(
        query,
        limit=top_k,
        allowed_source_filenames=allowed_source_filenames,
    )

    print("\nretrieval_status:", context["status"])
    print("query_original:", context.get("query_original"))
    print("query_normalized:", context.get("query_normalized"))
    print("query_terms:", context.get("query_terms"))
    print("quoted_terms:", context.get("quoted_terms"))
    print("source_intent:", context.get("source_intent"))
    print("selected_corpus:", context.get("selected_corpus"))
    print("candidate_filenames:", context.get("candidate_filenames"))
    print("selected_filenames:", context.get("selected_filenames"))
    print("chunks:", [chunk["id"] for chunk in context["chunks"]])
    print("document_ids:", context.get("document_ids"))
    print("source_filenames:", context.get("source_filenames"))
    print("scores:", context.get("scores"))

    if retrieval_only:
        print("\nANSWER:\nRETRIEVAL_ONLY")
        return

    if context["status"] != "EVIDENCE_FOUND":
        print("\nANSWER:\nNO_EVIDENCE_FOR_ANSWER")
        return

    print("\nEnviando pregunta a LM Studio...\n")

    answer = ask_lmstudio(context["prompt"])

    print("ANSWER:\n")
    print(answer)


def interactive_loop(top_k: int, allowed_source_filenames: list[str] | None = None) -> None:
    print("RAG documental local listo.")
    print("Escribe una pregunta y pulsa Enter.")
    print("Comandos: /exit para salir, /quit para salir.\n")

    while True:
        try:
            query = input("Pregunta > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSaliendo.")
            break

        if query.lower() in {"/exit", "/quit", "exit", "quit"}:
            print("Saliendo.")
            break

        ask_once(query=query, top_k=top_k, allowed_source_filenames=allowed_source_filenames)
        print("\n" + "-" * 80 + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--query",
        default=None,
        help="Pregunta documental a resolver usando chunks locales. Si se omite, entra en modo interactivo.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="Número máximo de chunks recuperados",
    )
    parser.add_argument(
        "--allowed-source-filename",
        action="append",
        default=[],
        help="Restringe la búsqueda a filenames concretos. Se puede repetir.",
    )
    parser.add_argument(
        "--retrieval-only",
        action="store_true",
        help="Solo valida retrieval y trazas, sin llamar al modelo.",
    )
    args = parser.parse_args()

    if args.query:
        ask_once(
            query=args.query,
            top_k=args.top_k,
            allowed_source_filenames=args.allowed_source_filename,
            retrieval_only=args.retrieval_only,
        )
        return

    interactive_loop(
        top_k=args.top_k,
        allowed_source_filenames=args.allowed_source_filename,
    )


if __name__ == "__main__":
    main()
