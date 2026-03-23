# HTML Downloader

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
│   └── processed/
├── html_downloader/
├── text_processing/
├── seed_urls.txt
├── requirements.txt
├── README.md
├── DEPLOYMENT.md
└── RELEASE_NOTES.md
```

`html_downloader/` содержит код загрузчика и точку входа для запуска.
`text_processing/` содержит второй этап: извлечение текста, токенизацию и лемматизацию.
`data/raw/` хранит HTML первого этапа, `data/processed/` хранит результаты обработки текста.
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

- `tokens.txt`
- `lemmas.txt`

## Второй этап

После того как HTML уже лежит в `data/raw/`, можно запустить обработку текста:

```bash
python -m text_processing
```

Скрипт:

- убирает содержимое `script`, `style` и `noscript`
- извлекает текст из HTML через BeautifulSoup
- собирает один общий список уникальных токенов
- лемматизирует токены через NLTK
- сохраняет результат в `data/processed/tokens.txt` и `data/processed/lemmas.txt`

При первом запуске `text_processing` NLTK-данные скачиваются локально в `data/nltk_data/`.
