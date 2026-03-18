from __future__ import annotations

import argparse
import logging
from pathlib import Path

import requests

HTML_CONTENT_TYPES = ("text/html", "application/xhtml+xml")
DEFAULT_SEED_FILE = Path("seed_urls.txt")
DEFAULT_OUTPUT_DIR = Path("data/raw")
DEFAULT_TARGET_COUNT = 100
DEFAULT_TIMEOUT = 15.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download raw HTML pages from a predefined URL list."
    )
    parser.add_argument(
        "--seed-file",
        type=Path,
        default=DEFAULT_SEED_FILE,
        help="Path to a text file with one URL per line.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where HTML files and index.txt will be written.",
    )
    parser.add_argument(
        "--target-count",
        type=int,
        default=DEFAULT_TARGET_COUNT,
        help="Maximum number of successful HTML pages to save.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help="HTTP timeout in seconds for each request.",
    )
    return parser.parse_args()


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def load_urls(seed_file: Path) -> list[str]:
    if not seed_file.exists():
        raise FileNotFoundError(f"Seed file not found: {seed_file}")

    urls: list[str] = []
    seen_urls: set[str] = set()

    with seed_file.open("r", encoding="utf-8") as file:
        for line_number, raw_line in enumerate(file, start=1):
            url = raw_line.strip()

            if not url or url.startswith("#"):
                continue

            if not url.startswith(("http://", "https://")):
                logging.warning(
                    "Skipped line %s in %s: not an HTTP URL (%s)",
                    line_number,
                    seed_file,
                    url,
                )
                continue

            if url in seen_urls:
                continue

            seen_urls.add(url)
            urls.append(url)

    if not urls:
        raise ValueError(f"No valid URLs found in {seed_file}")

    return urls


def prepare_output_dir(output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)

    for html_file in output_dir.glob("*.html"):
        html_file.unlink()

    index_file = output_dir / "index.txt"
    if index_file.exists():
        index_file.unlink()

    return index_file


def is_html_response(response: requests.Response) -> bool:
    content_type = response.headers.get("Content-Type", "").lower()
    return any(html_type in content_type for html_type in HTML_CONTENT_TYPES)


def build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "html-downloader-mvp/0.1",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        }
    )
    return session


def download_pages(
    urls: list[str],
    output_dir: Path,
    target_count: int,
    timeout: float,
) -> int:
    index_file = prepare_output_dir(output_dir)
    saved_count = 0

    with build_session() as session, index_file.open("w", encoding="utf-8") as index:
        for url in urls:
            if saved_count >= target_count:
                break

            try:
                response = session.get(url, timeout=timeout, allow_redirects=True)
            except requests.RequestException as error:
                logging.warning("Skipped %s: request failed (%s)", url, error)
                continue

            if not response.ok:
                logging.warning(
                    "Skipped %s: unexpected status code %s",
                    url,
                    response.status_code,
                )
                continue

            if not is_html_response(response):
                logging.warning(
                    "Skipped %s: unexpected content-type %s",
                    url,
                    response.headers.get("Content-Type", "missing"),
                )
                continue

            if not response.content or not response.content.strip():
                logging.warning("Skipped %s: empty response body", url)
                continue

            filename = f"{saved_count + 1:04d}.html"
            html_path = output_dir / filename

            try:
                html_path.write_bytes(response.content)
            except OSError as error:
                logging.warning("Skipped %s: failed to write %s (%s)", url, html_path, error)
                continue

            index.write(f"{filename} {url}\n")
            index.flush()

            saved_count += 1
            logging.info("Saved %s as %s", url, filename)

    logging.info(
        "Finished: saved %s HTML page(s) to %s",
        saved_count,
        output_dir,
    )
    return saved_count


def main() -> int:
    configure_logging()
    args = parse_args()

    if args.target_count <= 0:
        logging.error("--target-count must be greater than zero")
        return 1

    if args.timeout <= 0:
        logging.error("--timeout must be greater than zero")
        return 1

    try:
        urls = load_urls(args.seed_file)
    except (FileNotFoundError, OSError, ValueError) as error:
        logging.error("%s", error)
        return 1

    logging.info("Loaded %s unique URL(s) from %s", len(urls), args.seed_file)
    saved_count = download_pages(
        urls=urls,
        output_dir=args.output_dir,
        target_count=args.target_count,
        timeout=args.timeout,
    )

    if saved_count == 0:
        logging.error("No HTML pages were downloaded successfully")
        return 1

    if saved_count < args.target_count:
        logging.warning(
            "Requested %s page(s), but only saved %s. Add more working HTML URLs to %s if needed.",
            args.target_count,
            saved_count,
            args.seed_file,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
