from __future__ import annotations

from collections import Counter

from nltk.stem import WordNetLemmatizer

from text_processing.pipeline import (
    DEFAULT_NLTK_DATA_DIR,
    build_stop_words,
    ensure_nltk_data,
    extract_filtered_tokens,
    lemmatize_token,
)


def build_query_vector(
    query: str,
    idf: dict[str, float],
) -> tuple[str, dict[str, float]]:
    ensure_nltk_data(DEFAULT_NLTK_DATA_DIR)

    stop_words = build_stop_words()
    lemmatizer = WordNetLemmatizer()
    query_tokens = extract_filtered_tokens(query, stop_words)

    if not query_tokens:
        return "", {}

    query_lemmas = [lemmatize_token(token, lemmatizer) for token in query_tokens]
    lemma_counts = Counter(query_lemmas)
    total_terms = len(query_lemmas)

    vector: dict[str, float] = {}
    for lemma, count in sorted(lemma_counts.items()):
        lemma_idf = idf.get(lemma)
        if lemma_idf is None:
            continue
        tf = count / total_terms
        vector[lemma] = tf * lemma_idf

    normalized_query = " ".join(sorted(lemma_counts))
    return normalized_query, vector

