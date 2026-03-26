# Text Search Project

Простой скрипт, который берет список Wikipedia URL, скачивает HTML-страницы и раскладывает их по файлам.
В репозитории уже есть готовый список URL по военной истории XX века: бои, операции и командующие.

## Что делает проект

- читает URL из `seed_urls.txt`
- пропускает пустые строки, комментарии и дубликаты
- скачивает страницы по одной
- сохраняет только успешные HTML-ответы
- пишет файлы в `data/raw/0001.html`, `0002.html`, ...
- собирает `data/raw/index.txt` в формате `filename url`
- не падает, если часть ссылок недоступна или не является HTML

## Как устроен

```text
.
├── data/
│   ├── raw/
│   ├── processed/
│   ├── index/
│   └── tfidf/
├── html_downloader/
├── text_processing/
├── boolean_search/
├── tfidf/
├── vector_search/
├── search_web/
├── seed_urls.txt
├── requirements.txt
├── README.md
├── DEPLOYMENT.md
└── RELEASE_NOTES.md
```

`html_downloader/` содержит код загрузчика и точку входа для запуска.
`text_processing/` содержит второй этап: извлечение текста, токенизацию и лемматизацию.
`boolean_search/` содержит построение инвертированного индекса и булев поиск.
`tfidf/` содержит четвертый этап: расчет TF-IDF по терминам и леммам.
`vector_search/` содержит движок векторного поиска и ранжирование по cosine similarity.
`search_web/` содержит web-интерфейс поиска.
`data/raw/` хранит HTML первого этапа, `data/processed/` хранит пофайловые токены и леммы, `data/index/` хранит инвертированный индекс, `data/tfidf/` хранит TF-IDF.
`seed_urls.txt` содержит готовый список English Wikipedia URL по теме.

## Как запустить

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m html_downloader
```

## Где результат

После запуска в `data/raw/` появятся:

- `0001.html`, `0002.html`, ...
- `index.txt`

`index.txt` связывает имя файла с исходным URL.

После второго этапа в `data/processed/` появятся:

- `tokens/tokens_1.txt`, `tokens/tokens_2.txt`, ...
- `lemmas/lemmas_1.txt`, `lemmas/lemmas_2.txt`, ...

После третьего этапа в `data/index/` появится:

- `inverted_index.json`

После четвертого этапа в `data/tfidf/` появятся:

- `terms/terms_1.txt`, `terms/terms_2.txt`, ...
- `lemmas/lemmas_1.txt`, `lemmas/lemmas_2.txt`, ...

## Второй этап

После того как HTML уже лежит в `data/raw/`, можно запустить обработку текста:

```bash
python -m text_processing
```

Скрипт:

- убирает содержимое `script`, `style` и `noscript`
- извлекает текст из HTML через BeautifulSoup
- для каждого документа собирает свой набор уникальных токенов
- для каждого документа группирует токены по леммам через NLTK
- сохраняет результат в `data/processed/tokens/tokens_<N>.txt` и `data/processed/lemmas/lemmas_<N>.txt`

При первом запуске `text_processing` NLTK-данные скачиваются локально в `data/nltk_data/`.

## Третий этап

После того как корпус уже лежит в `data/raw/`, можно построить инвертированный индекс и выполнить булев поиск:

```bash
python -m boolean_search --build-index
python -m boolean_search "(kursk AND tank) OR rommel"
```

Скрипт:

- строит `lemma -> list of document ids` по документам корпуса
- сохраняет индекс в `data/index/inverted_index.json`
- перед поиском лемматизирует термины запроса
- поддерживает `AND`, `OR`, `NOT` и круглые скобки
- выводит нормализованный запрос, список найденных документов и их количество

## Четвертый этап

После того как корпус уже лежит в `data/raw/`, можно посчитать TF-IDF:

```bash
python -m tfidf
```

Скрипт:

- считает по каждому документу `tf(term, doc) = count(term in doc) / total_terms(doc)`
- считает `idf(term)` по всему корпусу
- считает `tf-idf(term, doc) = tf * idf`
- считает TF-IDF для лемм, где `tf(lemma, doc)` использует сумму вхождений всех токенов леммы
- сохраняет пофайловые результаты в `data/tfidf/terms/terms_<N>.txt` и `data/tfidf/lemmas/lemmas_<N>.txt`

## Пятый этап

После того как TF-IDF для лемм уже посчитан, можно запустить web-поиск:

```bash
uvicorn search_web.main:app --reload
```

Что делает этап:

- загружает векторы документов из `data/tfidf/lemmas/lemmas_<N>.txt`
- нормализует запрос: lowercase, токенизация, удаление stop words, лемматизация
- строит вектор запроса в пространстве лемм корпуса
- ранжирует документы по cosine similarity
- показывает топ-10 результатов (document id, score, URL из `data/raw/index.txt`, если есть)
