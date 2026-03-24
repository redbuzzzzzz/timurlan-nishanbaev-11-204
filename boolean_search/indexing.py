from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from text_processing.pipeline import (
    DEFAULT_NLTK_DATA_DIR,
    build_stop_words,
    collect_html_files,
    ensure_nltk_data,
    extract_text_from_html,
    tokenize_text,
)


@dataclass(frozen=True)
class InvertedIndexData:
    documents: list[str]
    index: dict[str, list[str]]


@dataclass(frozen=True)
class IndexSummary:
    documents: int
    terms: int
    output_path: Path


def build_inverted_index(
    input_dir: Path,
    nltk_data_dir: Path = DEFAULT_NLTK_DATA_DIR,
) -> InvertedIndexData:
    ensure_nltk_data(nltk_data_dir)

    html_files = collect_html_files(input_dir)
    stop_words = build_stop_words()
    postings: dict[str, set[str]] = defaultdict(set)
    document_ids = [html_file.name for html_file in html_files]

    for html_file in html_files:
        html = html_file.read_text(encoding="utf-8", errors="ignore")
        text = extract_text_from_html(html)
        tokens = tokenize_text(text, stop_words)

        for token in tokens:
            postings[token].add(html_file.name)

    sorted_index = {
        term: sorted(documents)
        for term, documents in sorted(postings.items())
    }

    return InvertedIndexData(documents=document_ids, index=sorted_index)


def save_inverted_index(index_data: InvertedIndexData, output_path: Path) -> IndexSummary:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "documents": index_data.documents,
        "index": index_data.index,
    }
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return IndexSummary(
        documents=len(index_data.documents),
        terms=len(index_data.index),
        output_path=output_path,
    )


def load_inverted_index(index_path: Path) -> InvertedIndexData:
    if not index_path.exists():
        raise FileNotFoundError(f"Inverted index not found: {index_path}")

    try:
        payload = json.loads(index_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid JSON in inverted index: {index_path}") from error

    documents = payload.get("documents")
    index = payload.get("index")

    if not isinstance(documents, list) or not isinstance(index, dict):
        raise ValueError(f"Invalid inverted index structure in {index_path}")

    normalized_documents = sorted({str(document) for document in documents})
    normalized_index: dict[str, list[str]] = {}
    for term, doc_ids in index.items():
        if not isinstance(doc_ids, list):
            raise ValueError(f"Invalid postings list for term '{term}' in {index_path}")
        normalized_index[str(term)] = sorted({str(doc_id) for doc_id in doc_ids})

    return InvertedIndexData(documents=normalized_documents, index=normalized_index)
