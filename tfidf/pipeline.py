from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

from text_processing.pipeline import (
    DEFAULT_NLTK_DATA_DIR,
    collect_document_frequency_results,
)


@dataclass(frozen=True)
class DocumentStats:
    document_id: str
    output_index: int
    total_terms: int
    term_counts: dict[str, int]
    lemma_counts: dict[str, int]


@dataclass(frozen=True)
class TfidfSummary:
    documents: int
    terms_dir: Path
    lemmas_dir: Path


def collect_document_stats(
    input_dir: Path,
    nltk_data_dir: Path = DEFAULT_NLTK_DATA_DIR,
) -> list[DocumentStats]:
    document_frequency_results = collect_document_frequency_results(
        input_dir, nltk_data_dir
    )
    return [
        DocumentStats(
            document_id=result.document_id,
            output_index=result.output_index,
            total_terms=result.total_terms,
            term_counts=result.term_counts,
            lemma_counts=result.lemma_counts,
        )
        for result in document_frequency_results
    ]


def build_idf(values_per_document: list[set[str]]) -> dict[str, float]:
    documents_count = len(values_per_document)
    document_frequency: dict[str, int] = {}
    for values in values_per_document:
        for value in values:
            document_frequency[value] = document_frequency.get(value, 0) + 1

    idf: dict[str, float] = {}
    for value, frequency in document_frequency.items():
        idf[value] = math.log(documents_count / frequency)
    return idf


def prepare_tfidf_output_dirs(output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    terms_dir = output_dir / "terms"
    lemmas_dir = output_dir / "lemmas"

    for directory in (terms_dir, lemmas_dir):
        directory.mkdir(parents=True, exist_ok=True)
        for txt_file in directory.glob("*.txt"):
            txt_file.unlink()

    return terms_dir, lemmas_dir


def write_term_tfidf(
    term_counts: dict[str, int],
    total_terms: int,
    term_idf: dict[str, float],
    output_path: Path,
) -> None:
    lines = []
    if total_terms > 0:
        for term in sorted(term_counts):
            tf = term_counts[term] / total_terms
            idf = term_idf[term]
            tf_idf = tf * idf
            lines.append(f"{term} {idf:.6f} {tf_idf:.6f}")

    content = "\n".join(lines)
    if content:
        content += "\n"
    output_path.write_text(content, encoding="utf-8")


def write_lemma_tfidf(
    lemma_counts: dict[str, int],
    total_terms: int,
    lemma_idf: dict[str, float],
    output_path: Path,
) -> None:
    lines = []
    if total_terms > 0:
        for lemma in sorted(lemma_counts):
            tf = lemma_counts[lemma] / total_terms
            idf = lemma_idf[lemma]
            tf_idf = tf * idf
            lines.append(f"{lemma} {idf:.6f} {tf_idf:.6f}")

    content = "\n".join(lines)
    if content:
        content += "\n"
    output_path.write_text(content, encoding="utf-8")


def process_corpus(
    input_dir: Path,
    output_dir: Path,
    nltk_data_dir: Path = DEFAULT_NLTK_DATA_DIR,
) -> TfidfSummary:
    document_stats = collect_document_stats(input_dir, nltk_data_dir)
    terms_dir, lemmas_dir = prepare_tfidf_output_dirs(output_dir)

    term_idf = build_idf([set(doc.term_counts) for doc in document_stats])
    lemma_idf = build_idf([set(doc.lemma_counts) for doc in document_stats])

    for document in document_stats:
        write_term_tfidf(
            term_counts=document.term_counts,
            total_terms=document.total_terms,
            term_idf=term_idf,
            output_path=terms_dir / f"terms_{document.output_index}.txt",
        )
        write_lemma_tfidf(
            lemma_counts=document.lemma_counts,
            total_terms=document.total_terms,
            lemma_idf=lemma_idf,
            output_path=lemmas_dir / f"lemmas_{document.output_index}.txt",
        )

    return TfidfSummary(
        documents=len(document_stats),
        terms_dir=terms_dir,
        lemmas_dir=lemmas_dir,
    )
