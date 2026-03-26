# Release Notes

## Version 5.0

- adding vector search over lemma TF-IDF vectors
- ranking by cosine similarity and returning top-10 results
- adding web interface with FastAPI and Jinja2 (`search_web`)

## Version 4.0

- calculating per-document TF-IDF for terms from `data/raw/*.html`
- calculating per-document TF-IDF for lemmas from the same documents
- saving term scores to `data/tfidf/terms/terms_<N>.txt`
- saving lemma scores to `data/tfidf/lemmas/lemmas_<N>.txt`

## Version 3.0

- building a lemma-based inverted index for `data/raw/*.html`
- saving `data/index/inverted_index.json`
- lemmatizing query terms before boolean search
- running boolean search with `AND`, `OR`, `NOT` and parentheses

## Version 2.0

- extracting text from `data/raw/*.html`
- saving per-document tokens to `data/processed/tokens/tokens_<N>.txt`
- saving per-document lemma groups to `data/processed/lemmas/lemmas_<N>.txt`

## Version 1.0

- downloading pages from `seed_urls.txt`
- saving raw HTML files to `data/raw/`
- generating `data/raw/index.txt`
