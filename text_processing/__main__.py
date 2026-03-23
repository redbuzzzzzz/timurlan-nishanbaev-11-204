from __future__ import annotations

import argparse
import logging
from pathlib import Path

DEFAULT_INPUT_DIR = Path("data/raw")
DEFAULT_OUTPUT_DIR = Path("data/processed")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract text from HTML files, build unique tokens, and group tokens by lemma."
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
        help="Directory for tokens.txt and lemmas.txt.",
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
    logging.info("Saved %s unique token(s) to %s", summary.tokens, summary.tokens_path)
    logging.info("Saved %s lemma group(s) to %s", summary.lemmas, summary.lemmas_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
