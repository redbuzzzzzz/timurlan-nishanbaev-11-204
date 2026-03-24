from __future__ import annotations

import argparse
import logging
from pathlib import Path

DEFAULT_INPUT_DIR = Path("data/raw")
DEFAULT_INDEX_FILE = Path("data/index/inverted_index.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build an inverted index and run boolean search over the corpus."
    )
    parser.add_argument(
        "query",
        nargs="?",
        help='Boolean query, for example: "(kursk AND tank) OR rommel"',
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=DEFAULT_INPUT_DIR,
        help="Directory with raw HTML files.",
    )
    parser.add_argument(
        "--index-file",
        type=Path,
        default=DEFAULT_INDEX_FILE,
        help="Path to inverted_index.json.",
    )
    parser.add_argument(
        "--build-index",
        action="store_true",
        help="Build the inverted index and exit.",
    )
    parser.add_argument(
        "--rebuild-index",
        action="store_true",
        help="Rebuild the inverted index before searching.",
    )
    return parser.parse_args()


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def main() -> int:
    configure_logging()
    args = parse_args()

    if not args.build_index and not args.query:
        logging.error("Provide a query or use --build-index")
        return 1

    try:
        from .indexing import build_inverted_index, load_inverted_index, save_inverted_index
        from .query import search_query
    except ModuleNotFoundError as error:
        logging.error(
            "Missing dependency: %s. Install project requirements before running boolean_search.",
            error.name,
        )
        return 1

    try:
        if args.build_index or args.rebuild_index or not args.index_file.exists():
            index_data = build_inverted_index(args.input_dir)
            summary = save_inverted_index(index_data, args.index_file)
            logging.info(
                "Saved inverted index with %s term(s) for %s document(s) to %s",
                summary.terms,
                summary.documents,
                summary.output_path,
            )
        else:
            index_data = load_inverted_index(args.index_file)

        if args.build_index and not args.query:
            return 0

        result = search_query(args.query, index_data)
    except (FileNotFoundError, RuntimeError, ValueError) as error:
        logging.error("%s", error)
        return 1

    print(f"Normalized query: {result.normalized_query}")
    print(f"Found {len(result.documents)} document(s)")
    for document_id in result.documents:
        print(document_id)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
