# Release Notes

## Version 3.0

- building a lemma-based inverted index for `data/raw/*.html`
- saving `data/index/inverted_index.json`
- lemmatizing query terms before boolean search
- running boolean search with `AND`, `OR`, `NOT` and parentheses

## Version 2.0

- extracting text from `data/raw/*.html`
- saving per-document tokens to `data/processed/tokens/<doc_id>.txt`
- saving per-document lemma groups to `data/processed/lemmas/<doc_id>.txt`

## Version 1.0

- downloading pages from `seed_urls.txt`
- saving raw HTML files to `data/raw/`
- generating `data/raw/index.txt`
