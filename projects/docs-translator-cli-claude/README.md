# Docs Translator CLI

CLI-утилита для перевода файлов документации через LibreTranslate-compatible REST API с локальным SQLite-хранилищем истории и пользовательским глоссарием.

## Возможности

- Перевод строк и текстовых файлов (`.md`, `.txt`, `.rst`) через REST API
- Определение языка текста через REST API
- Просмотр поддерживаемых языков
- Пользовательский глоссарий терминов с placeholder-механизмом
- Сохранение истории переводов в SQLite
- Экспорт истории в JSON, CSV, Markdown
- Конфигурация через CLI-опции, переменные окружения и JSON-файл
- Защита Markdown code blocks от перевода
- Покобайтная сегментация больших файлов для API
- Логирование в ротируемый файл (без API key)

## Требования

- Python 3.12
- [uv](https://docs.astral.sh/uv/) — менеджер проекта

## Установка

```bash
git clone <repo>
cd docs-translator-cli
uv sync
```

## Конфигурация

### API key и базовый URL

```bash
# Через CLI-опции (наивысший приоритет)
uv run docstrans --api-key YOUR_KEY translate-text "Hello" --source en --target ru

# Через переменные окружения
export DOCSTRANS_API_KEY=your_key
export DOCSTRANS_BASE_URL=https://libretranslate.com

# Через config-файл (сохраняется между запусками)
uv run docstrans config-set api_key YOUR_KEY
uv run docstrans config-set base_url https://libretranslate.com
```

Приоритет: CLI-опция > переменная окружения > config-файл > значение по умолчанию.

### Переменные окружения

| Переменная | Назначение |
|---|---|
| `DOCSTRANS_BASE_URL` | Базовый URL API |
| `DOCSTRANS_API_KEY` | API key |
| `DOCSTRANS_DEFAULT_SOURCE` | Исходный язык по умолчанию |
| `DOCSTRANS_DEFAULT_TARGET` | Целевой язык по умолчанию |
| `DOCSTRANS_TIMEOUT_SECONDS` | Timeout HTTP-запросов |
| `DOCSTRANS_DB_PATH` | Путь к SQLite DB |
| `DOCSTRANS_CONFIG_PATH` | Путь к config-файлу |
| `DOCSTRANS_LOG_LEVEL` | Уровень логирования: DEBUG, INFO, WARNING, ERROR |

Скопируйте `.env.example` → `.env` и настройте под себя. CLI `.env` автоматически не читает — экспортируйте переменные вручную или через `source .env`.

## Таблица команд

| Команда | REST API endpoint | Описание |
|---|---|---|
| `translate-text` | POST `/translate` | Перевод строки |
| `translate-file` | POST `/translate` | Перевод файла |
| `detect-language` | POST `/detect` | Определение языка |
| `languages-list` | GET `/languages` | Список языков |
| `glossary-add` | — | Добавить термин в глоссарий |
| `glossary-list` | — | Показать глоссарий |
| `glossary-remove` | — | Удалить термин из глоссария |
| `history-list` | — | История переводов |
| `export-history` | — | Экспорт истории |
| `config-set` | — | Установить настройку |
| `config-show` | — | Показать конфигурацию |
| `doctor` | GET `/health` | Проверка окружения и API |

## Примеры

```bash
# Проверить окружение
uv run docstrans doctor --skip-api

# Показать конфигурацию
uv run docstrans config-show

# Установить локальный LibreTranslate
uv run docstrans config-set base_url http://localhost:5000

# Перевести строку
uv run docstrans translate-text "Configure the deployment pipeline" --source en --target ru

# Перевести файл (README.md → README.ru.md)
uv run docstrans translate-file README.md --source en --target ru

# Перевести файл, перезаписать существующий
uv run docstrans translate-file docs/install.md --source en --target ru --overwrite

# Определить язык текста
uv run docstrans detect-language "Bonjour tout le monde"

# Список поддерживаемых языков
uv run docstrans languages-list

# Добавить термин в глоссарий
uv run docstrans glossary-add "deployment pipeline" "конвейер развертывания" \
    --source-lang en --target-lang ru

# Список терминов глоссария
uv run docstrans glossary-list --source-lang en --target-lang ru

# Удалить термин
uv run docstrans glossary-remove "deployment pipeline" --source-lang en --target-lang ru

# История переводов
uv run docstrans history-list --limit 10

# Экспорт истории
uv run docstrans export-history history.json --format json --overwrite
uv run docstrans export-history history.csv --format csv
uv run docstrans export-history history.md  --format md

# JSON-вывод для скриптов
uv run docstrans translate-text "Hello" --source en --target ru --json
uv run docstrans config-show --json
```

## REST API endpoints

Проект использует LibreTranslate-compatible API:

| Endpoint | Метод | Описание |
|---|---|---|
| `/translate` | POST | Перевод текста или массива сегментов |
| `/detect` | POST | Определение языка |
| `/languages` | GET | Список поддерживаемых языков |
| `/health` | GET | Проверка доступности API |

Базовый URL по умолчанию: `https://libretranslate.com`

## SQLite-хранилище

Путь по умолчанию (Linux): `~/.local/share/docs-translator-cli/docs-translator.sqlite3`

Таблицы:
- `glossary_terms` — пользовательский глоссарий
- `translation_history` — история переводов
- `schema_migrations` — версии схемы

## Запуск LibreTranslate локально

Если публичный API недоступен или нужен ключ:

```bash
docker run -it --rm -p 5000:5000 libretranslate/libretranslate
```

Затем:

```bash
uv run docstrans config-set base_url http://localhost:5000
uv run docstrans doctor
uv run docstrans translate-text "Hello world" --source en --target ru
```

## Тестирование

```bash
# Запуск всех тестов с отчётом покрытия
uv run pytest

# Только линтинг
uv run ruff check .

# Проверка форматирования
uv run ruff format --check .
```

Тесты используют `respx` для мокирования HTTP-запросов. Реальных сетевых запросов нет.

## Типичные ошибки

| Ошибка | Причина | Решение |
|---|---|---|
| `Error: API key is missing or invalid` | Публичный libretranslate.com требует ключ | Задайте `DOCSTRANS_API_KEY` или используйте self-hosted |
| `Error: translation API timeout` | API не отвечает | Увеличьте `--timeout` или смените `--base-url` |
| `Error: translation API connection error` | DNS / сеть недоступна | Проверьте `--base-url`, запустите локальный LibreTranslate |
| `Error: Output file exists, use --overwrite` | Выходной файл уже существует | Добавьте флаг `--overwrite` |
| `Error: Term already exists` | Термин уже в глоссарии | Добавьте флаг `--replace` |
| exit code 12 | Rate limit API (429) | Снизьте частоту запросов или используйте self-hosted |

## Exit codes

| Код | Значение |
|---|---|
| 0 | Успех |
| 2 | Ошибка аргументов CLI |
| 3 | Ошибка конфигурации |
| 4 | Данные не найдены |
| 5 | Ошибка файла |
| 6 | Конфликт данных |
| 10 | Сетевая ошибка |
| 11 | Ошибка авторизации API |
| 12 | Rate limit API |
| 13 | Некорректный запрос к API |
| 14 | Ошибка сервера API |
| 20 | Внутренняя ошибка |

## Лицензия

MIT
