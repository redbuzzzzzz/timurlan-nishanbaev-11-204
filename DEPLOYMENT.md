# Deployment

## 1. Создать виртуальное окружение

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 2. Установить зависимости

```bash
pip install -r requirements.txt
```

## 3. Запустить скрипт

```bash
python -m html_downloader
```

Результат первого этапа появится в `data/raw/`.

## 4. Запустить обработку текста

```bash
python -m text_processing
```

Результат второго этапа появится в `data/processed/tokens/` и `data/processed/lemmas/`.

## 5. Построить индекс и выполнить поиск

```bash
python -m boolean_search --build-index
python -m boolean_search "(kursk AND tank) OR rommel"
```

Индекс появится в `data/index/`, поиск идет по леммам, результаты выводятся в консоль.

## 6. Посчитать TF-IDF

```bash
python -m tfidf
```

Результат четвертого этапа появится в `data/tfidf/terms/` и `data/tfidf/lemmas/`.

## 7. Запустить web-поиск

```bash
uvicorn search_web.main:app --reload
```

Интерфейс откроется на `http://127.0.0.1:8000/`, поиск выводит top-10 документов.

Если нужно использовать свой набор ссылок, замените содержимое `seed_urls.txt` перед запуском.
