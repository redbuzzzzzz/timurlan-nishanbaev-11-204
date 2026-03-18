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

Результат появится в `data/raw/`.

Если нужно использовать свой набор ссылок, замените содержимое `seed_urls.txt` перед запуском.