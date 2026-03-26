from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path

LEMMA_FILE_RE = re.compile(r"^lemmas_(\d+)\.txt$")


@dataclass(frozen=True)
class CorpusVectors:
    document_vectors: dict[str, dict[str, float]]
    document_norms: dict[str, float]
    idf: dict[str, float]
    url_by_document: dict[str, str]


def load_corpus_vectors(
    lemmas_tfidf_dir: Path,
    raw_dir: Path,
    raw_index_path: Path,
) -> CorpusVectors:
    raw_document_ids = collect_raw_document_ids(raw_dir)
    url_by_document = load_raw_index(raw_index_path)

    document_vectors: dict[str, dict[str, float]] = {}
    idf: dict[str, float] = {}

    lemma_files = sorted(lemmas_tfidf_dir.glob("lemmas_*.txt"), key=lemma_file_key)
    for lemma_file in lemma_files:
        match = LEMMA_FILE_RE.match(lemma_file.name)
        if not match:
            continue
        position = int(match.group(1))
        if position < 1 or position > len(raw_document_ids):
            continue

        document_id = raw_document_ids[position - 1]
        vector, local_idf = parse_lemma_tfidf_file(lemma_file)
        document_vectors[document_id] = vector

        for lemma, lemma_idf in local_idf.items():
            if lemma not in idf:
                idf[lemma] = lemma_idf

    document_norms = {
        document_id: math.sqrt(sum(weight * weight for weight in vector.values()))
        for document_id, vector in document_vectors.items()
    }

    return CorpusVectors(
        document_vectors=document_vectors,
        document_norms=document_norms,
        idf=idf,
        url_by_document=url_by_document,
    )


def collect_raw_document_ids(raw_dir: Path) -> list[str]:
    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw directory not found: {raw_dir}")

    document_ids = sorted(path.name for path in raw_dir.glob("*.html"))
    if not document_ids:
        raise ValueError(f"No HTML files found in {raw_dir}")
    return document_ids


def load_raw_index(raw_index_path: Path) -> dict[str, str]:
    if not raw_index_path.exists():
        return {}

    mapping: dict[str, str] = {}
    for line in raw_index_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        parts = stripped.split(maxsplit=1)
        if len(parts) != 2:
            continue
        document_id, url = parts
        mapping[document_id] = url
    return mapping


def parse_lemma_tfidf_file(path: Path) -> tuple[dict[str, float], dict[str, float]]:
    vector: dict[str, float] = {}
    idf: dict[str, float] = {}

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        parts = stripped.split()
        if len(parts) != 3:
            continue
        lemma, idf_value, tfidf_value = parts
        vector[lemma] = float(tfidf_value)
        idf[lemma] = float(idf_value)

    return vector, idf


def lemma_file_key(path: Path) -> tuple[int, str]:
    match = LEMMA_FILE_RE.match(path.name)
    if not match:
        return (10**9, path.name)
    return (int(match.group(1)), path.name)

