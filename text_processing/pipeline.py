from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import nltk
from bs4 import BeautifulSoup
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

TOKEN_RE = re.compile(r"[a-z]+")
ROMAN_NUMERAL_RE = re.compile(
    r"^m{0,4}(cm|cd|d?c{0,3})(xc|xl|l?x{0,3})(ix|iv|v?i{1,3})$"
)
REPEATED_CHAR_RE = re.compile(r"^(.)\1+$")
DEFAULT_NLTK_DATA_DIR = Path("data/nltk_data")
REQUIRED_NLTK_DATA = {
    "stopwords": ("corpora/stopwords", "corpora/stopwords.zip"),
    "wordnet": ("corpora/wordnet", "corpora/wordnet.zip"),
    "omw-1.4": ("corpora/omw-1.4", "corpora/omw-1.4.zip"),
}
EXTRA_STOPWORDS = {
    "archived",
    "caption",
    "cite",
    "citation",
    "com",
    "copyright",
    "edit",
    "encyclopedia",
    "file",
    "html",
    "hide",
    "http",
    "https",
    "isbn",
    "issn",
    "jump",
    "navigation",
    "org",
    "page",
    "pages",
    "pdf",
    "png",
    "ref",
    "refs",
    "retrieved",
    "show",
    "sidebar",
    "svg",
    "toggle",
    "url",
    "via",
    "web",
    "webarchive",
    "wikipedia",
    "www",
}


@dataclass(frozen=True)
class ProcessingSummary:
    documents: int
    tokens: int
    lemmas: int
    tokens_path: Path
    lemmas_path: Path


def ensure_nltk_data(nltk_data_dir: Path = DEFAULT_NLTK_DATA_DIR) -> None:
    nltk_data_dir.mkdir(parents=True, exist_ok=True)
    nltk_path = str(nltk_data_dir.resolve())
    if nltk_path not in nltk.data.path:
        nltk.data.path.insert(0, nltk_path)

    for package_name, resource_paths in REQUIRED_NLTK_DATA.items():
        if nltk_resource_exists(resource_paths):
            continue

        if not nltk.download(package_name, download_dir=nltk_path, quiet=True):
            raise RuntimeError(
                f"Could not download required NLTK data package: {package_name}"
            ) from None

        if not nltk_resource_exists(resource_paths):
            raise RuntimeError(
                f"NLTK data package is still unavailable after download: {package_name}"
            )


def nltk_resource_exists(resource_paths: tuple[str, ...]) -> bool:
    for resource_path in resource_paths:
        try:
            nltk.data.find(resource_path)
            return True
        except LookupError:
            continue

    return False


def collect_html_files(input_dir: Path) -> list[Path]:
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    html_files = sorted(input_dir.glob("*.html"))
    if not html_files:
        raise ValueError(f"No HTML files found in {input_dir}")

    return html_files


def extract_text_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    root = (
        soup.select_one("#mw-content-text .mw-parser-output")
        or soup.select_one("#mw-content-text")
        or soup.select_one("main")
        or soup.body
        or soup
    )

    for element in root.select(
        "script, style, noscript, nav, header, footer, div.reflist, "
        "ol.references, sup.reference, span.mw-editsection, table, "
        "div.navbox, table.navbox, table.metadata, div.catlinks, "
        "div.hatnote, div.shortdescription, div.thumb, div.sidebar, "
        "div.mbox-small, div.sistersitebox, div.metadata, div.toc"
    ):
        element.decompose()

    blocks = root.find_all(["p", "li"])
    if blocks:
        return " ".join(
            block.get_text(" ", strip=True)
            for block in blocks
            if block.get_text(" ", strip=True)
        )

    return root.get_text(" ", strip=True)


def build_stop_words() -> set[str]:
    return set(stopwords.words("english")) | EXTRA_STOPWORDS


def tokenize_text(text: str, stop_words: set[str]) -> set[str]:
    tokens = set()

    for token in TOKEN_RE.findall(text.lower()):
        if len(token) < 3:
            continue
        if token in stop_words:
            continue
        if REPEATED_CHAR_RE.fullmatch(token):
            continue
        if ROMAN_NUMERAL_RE.fullmatch(token):
            continue
        tokens.add(token)

    return tokens


def lemmatize_token(token: str, lemmatizer: WordNetLemmatizer) -> str:
    lemma = token
    for pos in ("v", "n", "a", "r"):
        lemma = lemmatizer.lemmatize(lemma, pos=pos)
    return lemma


def write_tokens(tokens: list[str], output_path: Path) -> None:
    output_path.write_text("\n".join(tokens) + "\n", encoding="utf-8")


def write_lemmas(lemma_groups: dict[str, list[str]], output_path: Path) -> None:
    lines = []
    for lemma in sorted(lemma_groups):
        grouped_tokens = " ".join(lemma_groups[lemma])
        lines.append(f"{lemma} {grouped_tokens}")

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def process_corpus(
    input_dir: Path,
    output_dir: Path,
    nltk_data_dir: Path = DEFAULT_NLTK_DATA_DIR,
) -> ProcessingSummary:
    ensure_nltk_data(nltk_data_dir)

    html_files = collect_html_files(input_dir)
    stop_words = build_stop_words()
    all_tokens: set[str] = set()

    for html_file in html_files:
        html = html_file.read_text(encoding="utf-8", errors="ignore")
        text = extract_text_from_html(html)
        all_tokens.update(tokenize_text(text, stop_words))

    sorted_tokens = sorted(all_tokens)
    lemmatizer = WordNetLemmatizer()
    lemma_map: dict[str, set[str]] = defaultdict(set)

    for token in sorted_tokens:
        lemma = lemmatize_token(token, lemmatizer)
        lemma_map[lemma].add(token)

    sorted_lemma_map = {
        lemma: sorted(tokens)
        for lemma, tokens in sorted(lemma_map.items())
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    tokens_path = output_dir / "tokens.txt"
    lemmas_path = output_dir / "lemmas.txt"

    write_tokens(sorted_tokens, tokens_path)
    write_lemmas(sorted_lemma_map, lemmas_path)

    return ProcessingSummary(
        documents=len(html_files),
        tokens=len(sorted_tokens),
        lemmas=len(sorted_lemma_map),
        tokens_path=tokens_path,
        lemmas_path=lemmas_path,
    )
