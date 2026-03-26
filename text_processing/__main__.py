from __future__ import annotations

import argparse
import logging
from pathlib import Path

DEFAULT_INPUT_DIR = Path("data/raw")
DEFAULT_OUTPUT_DIR = Path("data/processed")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract text from HTML files and save per-document tokens and lemmas."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=DEFAULT_INPUT_DIR,
        help="Directory with raw HTML files.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for per-document tokens and lemmas.",
    )
    return parser.parse_args()


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def main() -> int:
    configure_logging()
    args = parse_args()

    try:
        from .pipeline import process_corpus
    except ModuleNotFoundError as error:
        logging.error(
            "Missing dependency: %s. Install project requirements before running text_processing.",
            error.name,
        )
        return 1

    try:
        summary = process_corpus(args.input_dir, args.output_dir)
    except (FileNotFoundError, RuntimeError, ValueError) as error:
        logging.error("%s", error)
        return 1

    logging.info("Processed %s HTML file(s)", summary.documents)
    logging.info("Saved per-document tokens to %s", summary.tokens_dir)
    logging.info("Saved per-document lemmas to %s", summary.lemmas_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
