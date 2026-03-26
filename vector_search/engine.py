from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

from .loader import CorpusVectors, load_corpus_vectors
from .query_processing import build_query_vector

DEFAULT_LEMMAS_TFIDF_DIR = Path("data/tfidf/lemmas")
DEFAULT_RAW_DIR = Path("data/raw")
DEFAULT_RAW_INDEX_PATH = Path("data/raw/index.txt")


@dataclass(frozen=True)
class SearchHit:
    document_id: str
    score: float
    url: str


@dataclass(frozen=True)
class SearchResult:
    normalized_query: str
    hits: list[SearchHit]
    message: str


class VectorSearchEngine:
    def __init__(
        self,
        lemmas_tfidf_dir: Path = DEFAULT_LEMMAS_TFIDF_DIR,
        raw_dir: Path = DEFAULT_RAW_DIR,
        raw_index_path: Path = DEFAULT_RAW_INDEX_PATH,
    ) -> None:
        self.corpus: CorpusVectors = load_corpus_vectors(
            lemmas_tfidf_dir=lemmas_tfidf_dir,
            raw_dir=raw_dir,
            raw_index_path=raw_index_path,
        )

    def search(self, query: str, top_k: int = 10) -> SearchResult:
        normalized_query, query_vector = build_query_vector(query, self.corpus.idf)

        if not query.strip():
            return SearchResult(
                normalized_query="",
                hits=[],
                message="Empty query. Enter one or more terms.",
            )

        if not query_vector:
            return SearchResult(
                normalized_query=normalized_query,
                hits=[],
                message=(
                    "No searchable terms after normalization, "
                    "or query terms are absent in the corpus."
                ),
            )

        query_norm = math.sqrt(sum(weight * weight for weight in query_vector.values()))
        if query_norm == 0.0:
            return SearchResult(
                normalized_query=normalized_query,
                hits=[],
                message="Query vector has zero length.",
            )

        scored_hits: list[SearchHit] = []
        for document_id, document_vector in self.corpus.document_vectors.items():
            document_norm = self.corpus.document_norms.get(document_id, 0.0)
            if document_norm == 0.0:
                continue

            dot_product = 0.0
            for lemma, query_weight in query_vector.items():
                document_weight = document_vector.get(lemma)
                if document_weight is None:
                    continue
                dot_product += query_weight * document_weight

            if dot_product <= 0.0:
                continue

            score = dot_product / (query_norm * document_norm)
            scored_hits.append(
                SearchHit(
                    document_id=document_id,
                    score=score,
                    url=self.corpus.url_by_document.get(document_id, ""),
                )
            )

        scored_hits.sort(key=lambda hit: hit.score, reverse=True)
        top_hits = scored_hits[:top_k]

        if not top_hits:
            return SearchResult(
                normalized_query=normalized_query,
                hits=[],
                message="No matching documents found.",
            )

        return SearchResult(
            normalized_query=normalized_query,
            hits=top_hits,
            message="",
        )

