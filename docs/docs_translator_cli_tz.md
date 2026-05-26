# Техническое задание на разработку проекта Docs Translator CLI

## 1. Общая информация

**Название проекта:** Docs Translator CLI  
**Имя Python-пакета:** `docstrans`  
**Имя исполняемой CLI-команды:** `docstrans`  
**Тип проекта:** консольная CLI-утилита на Python  
**Основная задача:** перевод текстовых файлов документации и отдельных строк через внешний REST API переводчика с локальным SQLite-хранилищем истории переводов и пользовательского глоссария терминов.

Проект должен быть реализован как полноценный Python-пакет с установкой через `uv`, запуском через консольную команду `docstrans`, документацией, тестами и воспроизводимой структурой репозитория.

## 2. Основание и обязательные требования преподавателя

Проект должен соответствовать следующим требованиям учебного задания:

1. CLI-утилита должна иметь практическую полезность и среднюю сложность.
2. Должно быть реализовано не менее 7 команд или подкоманд.
3. Использование REST API обязательно. Утилита без REST API считается неприемлемой.
4. В ТЗ и README должны быть явно описаны команды, аргументы, опции, примеры использования, ожидаемое поведение и соответствие команд REST API endpoints.
5. Должны быть описаны библиотеки, структура проекта, обработка ошибок, конфигурация, логирование и тестирование.
6. Должны быть написаны unit-тесты, минимум 5-10 тестов. В этом проекте требуется не менее 12 тестов.
7. Проект должен быть оформлен для публикации на GitHub: `README.md`, `.gitignore`, лицензия, тесты, понятная структура.

## 3. Выбранный стек и проверенные источники

Стек выбран минимальным, но достаточным для надежной реализации.

### 3.1. Язык и пакетный менеджер

- **Python:** `3.12`
- **Менеджер проекта:** `uv`
- **Формат проекта:** стандартный `pyproject.toml` + `src/` layout

Причина выбора `uv`: проект должен использовать пожелание заказчика по `uv`; `uv` официально поддерживает создание проектов, управление зависимостями, `uv run`, `uv sync`, `uv lock`, `uv build`.

Официальная документация:

- `uv`: https://docs.astral.sh/uv/guides/projects/

### 3.2. CLI

- **Typer** - построение CLI на основе type hints.
- **Rich** - таблицы, панели, аккуратный вывод ошибок и результатов.

Причина выбора: в учебных материалах отдельно выделены Typer, типизация аргументов, опции, вложенные команды и интеграция с Rich. Typer также генерирует help по type hints и подходит для учебного CLI.

Официальная документация:

- Typer: https://typer.tiangolo.com/
- Typer commands/arguments/options: https://typer.tiangolo.com/tutorial/commands/arguments/
- Rich tables: https://rich.readthedocs.io/en/latest/tables.html
- Rich progress: https://rich.readthedocs.io/en/latest/progress.html

### 3.3. REST API клиент

- **httpx** - синхронный HTTP-клиент.

Причина выбора: API-запросы простые и синхронные; `httpx.Client` дает нормальную работу с timeouts, статусами, исключениями и тестированием через RESPX.

Официальная документация:

- HTTPX quickstart/exceptions: https://www.python-httpx.org/quickstart/
- HTTPX timeouts: https://www.python-httpx.org/advanced/timeouts/
- HTTPX exceptions: https://www.python-httpx.org/exceptions/

### 3.4. Внешний REST API переводчика

Основной провайдер для реализации: **LibreTranslate-compatible API**.

По умолчанию используется `https://libretranslate.com`, но пользователь должен иметь возможность заменить URL на self-hosted LibreTranslate-инстанс через config/env/CLI-опцию. Это снижает риск недоступности публичного сервиса и делает проект проверяемым локально.

Используемые endpoints:

- `POST /translate`
- `POST /detect`
- `GET /languages`
- `GET /health`

Официальная документация:

- LibreTranslate API usage: https://docs.libretranslate.com/guides/api_usage/
- `POST /translate`: https://docs.libretranslate.com/api/operations/translate/
- `POST /detect`: https://docs.libretranslate.com/api/operations/detect/
- `GET /languages`: https://docs.libretranslate.com/api/operations/languages/
- `GET /health`: https://docs.libretranslate.com/api/operations/health/

### 3.5. Локальное хранилище

- **SQLite через стандартный модуль `sqlite3`**.
- **platformdirs** для кроссплатформенных путей к config/data/logs.

Официальная документация:

- Python `sqlite3`: https://docs.python.org/3/library/sqlite3.html
- platformdirs: https://platformdirs.readthedocs.io/

### 3.6. Тестирование и качество кода

- **pytest** - unit-тесты.
- **respx** - мокирование HTTPX-запросов к REST API.
- **ruff** - линтер и форматтер.

Официальная документация:

- pytest: https://docs.pytest.org/en/stable/
- RESPX: https://lundberg.github.io/respx/
- Ruff: https://docs.astral.sh/ruff/

## 4. Область реализации

### 4.1. Входит в проект

1. Перевод строки через REST API.
2. Перевод текстового файла документации через REST API.
3. Определение языка текста через REST API.
4. Просмотр поддерживаемых языков через REST API.
5. Проверка доступности API и локального хранилища.
6. Локальный пользовательский глоссарий терминов.
7. Применение глоссария перед переводом.
8. Локальная история переводов.
9. Экспорт истории в `json`, `csv`, `md`.
10. Конфигурация API URL, API key, языков по умолчанию и timeout.
11. Логирование ошибок в файл без утечки API key.
12. Unit-тесты без реальных сетевых запросов.

### 4.2. Не входит в проект

1. GUI-интерфейс.
2. Перевод PDF/DOCX/XLSX.
3. Машинный перевод без REST API.
4. Асинхронная очередь задач.
5. Авторизация пользователей.
6. Синхронизация истории между устройствами.
7. Веб-сервер или собственный backend.
8. Интеграция с DeepL как отдельным провайдером. Реализуется только LibreTranslate-compatible API, потому что он покрывает перевод и детект языка через простые REST endpoints.

## 5. Общая логика работы

CLI должен работать по следующей схеме:

1. Пользователь вызывает команду `docstrans ...`.
2. CLI загружает конфигурацию из CLI-опций, переменных окружения и config-файла.
3. CLI инициализирует SQLite-хранилище, если оно еще не создано.
4. Для команд перевода CLI читает глоссарий из SQLite.
5. CLI применяет глоссарий к входному тексту через placeholder-механизм.
6. CLI отправляет текст в LibreTranslate-compatible REST API.
7. CLI получает ответ API.
8. CLI восстанавливает термины глоссария в переводе.
9. CLI выводит результат в консоль или файл.
10. CLI сохраняет запись в историю переводов, если не указан `--no-save`.
11. При ошибке CLI выводит короткое понятное сообщение в stderr, пишет детали в log-файл и возвращает ненулевой exit code.

## 6. Требования к REST API

### 6.1. Базовый URL

По умолчанию:

```text
https://libretranslate.com
```

Пользователь может заменить базовый URL:

1. CLI-опцией `--base-url`.
2. Переменной окружения `DOCSTRANS_BASE_URL`.
3. Полем `base_url` в config-файле.

Приоритет: CLI-опция выше env, env выше config, config выше значения по умолчанию.

### 6.2. API key

LibreTranslate self-hosted может не требовать ключ. Публичный `libretranslate.com` может требовать API key. Поэтому ключ должен быть опциональным.

API key берется из:

1. CLI-опции `--api-key`.
2. Переменной окружения `DOCSTRANS_API_KEY`.
3. Поля `api_key` в config-файле.

API key нельзя выводить полностью в консоль и нельзя писать в лог.

### 6.3. Формат HTTP-запросов

Все запросы к `POST /translate` и `POST /detect` отправляются с заголовком:

```http
Content-Type: application/json
```

### 6.4. Endpoint: перевод текста

```http
POST {base_url}/translate
Content-Type: application/json
```

Тело запроса для одного текста:

```json
{
  "q": "Hello world",
  "source": "en",
  "target": "ru",
  "format": "text",
  "api_key": "..."
}
```

Тело запроса для пакетного перевода сегментов файла:

```json
{
  "q": ["First paragraph", "Second paragraph"],
  "source": "en",
  "target": "ru",
  "format": "text",
  "api_key": "..."
}
```

Поле `api_key` добавляется только если ключ реально задан.

Ожидаемый успешный ответ:

```json
{
  "translatedText": "Привет, мир"
}
```

Или для массива:

```json
{
  "translatedText": ["Первый абзац", "Второй абзац"]
}
```

### 6.5. Endpoint: определение языка

```http
POST {base_url}/detect
Content-Type: application/json
```

Тело запроса:

```json
{
  "q": "Bonjour"
}
```

Если `api_key` задан, тело запроса:

```json
{
  "q": "Bonjour",
  "api_key": "..."
}
```

Ожидаемый успешный ответ:

```json
[
  {
    "confidence": 90.0,
    "language": "fr"
  }
]
```

### 6.6. Endpoint: список языков

```http
GET {base_url}/languages
```

Ожидаемый успешный ответ:

```json
[
  {
    "code": "en",
    "name": "English",
    "targets": ["ru", "de", "fr"]
  }
]
```

### 6.7. Endpoint: health check

```http
GET {base_url}/health
```

Ожидаемый успешный ответ:

```json
{
  "status": "ok"
}
```

## 7. Глобальные CLI-опции

Все команды должны поддерживать глобальные опции, указываемые до команды:

```bash
docstrans [GLOBAL_OPTIONS] COMMAND [COMMAND_OPTIONS]
```

| Опция | Тип | Обязательность | Значение по умолчанию | Описание |
|---|---:|---:|---|---|
| `--config-path PATH` | `Path` | Нет | platformdirs config path | Путь к config-файлу. |
| `--db-path PATH` | `Path` | Нет | platformdirs data path | Путь к SQLite DB. |
| `--base-url URL` | `str` | Нет | из config/env или `https://libretranslate.com` | Базовый URL LibreTranslate-compatible API. |
| `--api-key TEXT` | `str` | Нет | из config/env или отсутствует | API key переводчика. В выводе маскируется. |
| `--timeout FLOAT` | `float` | Нет | `20.0` | Timeout HTTP-запросов в секундах. Должен быть `> 0`. |
| `--verbose` | `bool` | Нет | `False` | Более подробные ошибки в stderr и DEBUG-логи. |
| `--no-color` | `bool` | Нет | `False` | Отключить Rich-цвета. |

Пример:

```bash
docstrans --base-url http://localhost:5000 translate-text "Hello" --source en --target ru
```

## 8. Команды CLI

Нужно реализовать 11 команд:

1. `translate-text`
2. `translate-file`
3. `detect-language`
4. `languages-list`
5. `glossary-add`
6. `glossary-list`
7. `glossary-remove`
8. `history-list`
9. `export-history`
10. `config-set`
11. `config-show`
12. `doctor`

Команд получается больше минимального требования. Это не перегружает проект, потому что дополнительные команды нужны для конфигурации и проверки работоспособности.

---

## 9. Подробное описание команд

### 9.1. Команда `translate-text`

**Команда:**

```bash
docstrans translate-text TEXT [OPTIONS]
```

**Описание:**  
Переводит одну текстовую строку через REST API, применяет локальный глоссарий и сохраняет результат в историю.

**Аргументы:**

| Аргумент | Тип | Обязательность | Описание |
|---|---:|---:|---|
| `TEXT` | `str` | Да | Текст для перевода. Пустая строка запрещена. |

**Опции:**

| Опция | Тип | Обязательность | Значение по умолчанию | Описание |
|---|---:|---:|---|---|
| `--source`, `-s` | `str` | Нет | `auto` | Исходный язык. Например `en`, `ru`, `de`, `auto`. |
| `--target`, `-t` | `str` | Нет | из config или `ru` | Целевой язык. Например `ru`, `en`, `de`. |
| `--format` | enum: `text`, `html` | Нет | `text` | Формат текста для API. |
| `--output`, `-o` | `Path` | Нет | отсутствует | Если указан, сохранить перевод в файл. |
| `--no-save` | `bool` | Нет | `False` | Не сохранять перевод в историю. |
| `--json` | `bool` | Нет | `False` | Вывести машинно-читаемый JSON вместо обычного текста. |

**Используемый REST endpoint:**

```http
POST {base_url}/translate
```

**Тело запроса:**

```json
{
  "q": "TEXT after glossary placeholders",
  "source": "auto",
  "target": "ru",
  "format": "text",
  "api_key": "only if configured"
}
```

**Пример использования:**

```bash
docstrans translate-text "Open the configuration file" --source en --target ru
```

**Ожидаемый вывод в консоль:**

```text
Откройте файл конфигурации
```

**Пример JSON-вывода:**

```bash
docstrans translate-text "Open the configuration file" --source en --target ru --json
```

```json
{
  "source_language": "en",
  "target_language": "ru",
  "translated_text": "Откройте файл конфигурации",
  "provider": "libretranslate",
  "saved_to_history": true
}
```

**Ожидаемый результат:**

1. В консоль выведен перевод.
2. Если указан `--output`, создан UTF-8 файл с переводом.
3. Если не указан `--no-save`, в SQLite добавлена запись в таблицу `translation_history`.
4. Если перевод невозможен из-за API, команда возвращает соответствующий exit code.

---

### 9.2. Команда `translate-file`

**Команда:**

```bash
docstrans translate-file INPUT_PATH [OPTIONS]
```

**Описание:**  
Переводит текстовый файл документации через REST API, применяет глоссарий, сохраняет результат в новый файл и добавляет запись в историю.

**Аргументы:**

| Аргумент | Тип | Обязательность | Описание |
|---|---:|---:|---|
| `INPUT_PATH` | `Path` | Да | Путь к входному файлу. Файл должен существовать. |

**Опции:**

| Опция | Тип | Обязательность | Значение по умолчанию | Описание |
|---|---:|---:|---|---|
| `--source`, `-s` | `str` | Нет | `auto` | Исходный язык. |
| `--target`, `-t` | `str` | Нет | из config или `ru` | Целевой язык. |
| `--output`, `-o` | `Path` | Нет | auto-generated | Путь к выходному файлу. |
| `--overwrite` | `bool` | Нет | `False` | Разрешить перезапись существующего output-файла. |
| `--create-dirs` | `bool` | Нет | `False` | Создать родительские директории output-файла, если их нет. |
| `--encoding` | `str` | Нет | `utf-8` | Кодировка чтения и записи. |
| `--format` | enum: `text`, `html` | Нет | `text` | Формат текста для API. Для `.md` использовать `text`. |
| `--chunk-size` | `int` | Нет | `4000` | Максимальная длина одного сегмента для API. Минимум `500`, максимум `10000`. |
| `--batch-size` | `int` | Нет | `20` | Максимум сегментов в одном API-запросе. Минимум `1`, максимум `50`. |
| `--preserve-markdown-code` | `bool` | Нет | `True` | Не переводить fenced code blocks и inline code в Markdown. |
| `--no-save` | `bool` | Нет | `False` | Не сохранять запись в историю. |
| `--json` | `bool` | Нет | `False` | Вывести JSON-сводку. |

**Правило автоматического имени output-файла:**

Если `--output` не указан, файл создается рядом с исходным по шаблону:

```text
{input_stem}.{target_language}{input_suffix}
```

Примеры:

| Входной файл | Target | Output по умолчанию |
|---|---:|---|
| `README.md` | `ru` | `README.ru.md` |
| `docs/install.txt` | `en` | `docs/install.en.txt` |

**Поддерживаемые расширения:**

- `.txt`
- `.md`
- `.rst`

Если файл имеет другое расширение, команда должна продолжить работу, но вывести предупреждение:

```text
Warning: extension .log is not officially supported; processing as plain text.
```

**Markdown-правила:**

Для `.md` при `--preserve-markdown-code=True` CLI обязан:

1. Не переводить fenced code blocks, начинающиеся с ````` ``` ````` или `~~~`.
2. Не переводить inline code внутри одиночных backticks.
3. Не изменять URL вида `https://...` и `http://...`.
4. Переводить обычный текст, заголовки, пункты списков и абзацы.
5. Сохранять порядок строк и финальный newline, если он был во входном файле.

**Используемый REST endpoint:**

```http
POST {base_url}/translate
```

**Тело запроса:**

```json
{
  "q": ["segment 1", "segment 2"],
  "source": "auto",
  "target": "ru",
  "format": "text",
  "api_key": "only if configured"
}
```

**Пример использования:**

```bash
docstrans translate-file README.md --source en --target ru
```

**Ожидаемый вывод:**

```text
Translated file saved: README.ru.md
Segments translated: 12
History entry: saved
```

**Пример JSON-вывода:**

```json
{
  "input_path": "README.md",
  "output_path": "README.ru.md",
  "source_language": "en",
  "target_language": "ru",
  "segments_translated": 12,
  "provider": "libretranslate",
  "saved_to_history": true
}
```

**Ожидаемый результат:**

1. Создан output-файл с переводом.
2. Если output-файл существует и `--overwrite` не указан, команда завершается с exit code `5`.
3. Если `--create-dirs` указан, отсутствующие родительские директории output-файла создаются.
4. История сохраняет путь к исходному и выходному файлу, языки, provider, timestamp, hash исходного текста и hash результата.

---

### 9.3. Команда `detect-language`

**Команда:**

```bash
docstrans detect-language TEXT [OPTIONS]
```

**Описание:**  
Определяет язык переданного текста через REST API.

**Аргументы:**

| Аргумент | Тип | Обязательность | Описание |
|---|---:|---:|---|
| `TEXT` | `str` | Да | Текст для определения языка. Пустая строка запрещена. |

**Опции:**

| Опция | Тип | Обязательность | Значение по умолчанию | Описание |
|---|---:|---:|---|---|
| `--json` | `bool` | Нет | `False` | Вывести сырой JSON с вариантами языка. |

**Используемый REST endpoint:**

```http
POST {base_url}/detect
```

**Пример использования:**

```bash
docstrans detect-language "Bonjour tout le monde"
```

**Ожидаемый вывод:**

```text
Language: fr
Confidence: 90.0
```

**Пример JSON-вывода:**

```json
{
  "best": {
    "language": "fr",
    "confidence": 90.0
  },
  "detections": [
    {
      "language": "fr",
      "confidence": 90.0
    }
  ]
}
```

**Ожидаемый результат:**

1. Выполнен REST-запрос к `/detect`.
2. В консоль выведен наиболее вероятный язык.
3. История переводов не изменяется.

---

### 9.4. Команда `languages-list`

**Команда:**

```bash
docstrans languages-list [OPTIONS]
```

**Описание:**  
Показывает список языков, поддерживаемых текущим API endpoint.

**Опции:**

| Опция | Тип | Обязательность | Значение по умолчанию | Описание |
|---|---:|---:|---|---|
| `--json` | `bool` | Нет | `False` | Вывести JSON вместо таблицы. |
| `--target-for` | `str` | Нет | отсутствует | Показать только языки, доступные как target для указанного source. |

**Используемый REST endpoint:**

```http
GET {base_url}/languages
```

**Пример использования:**

```bash
docstrans languages-list
```

**Ожидаемый табличный вывод:**

```text
Code  Name      Targets
----  --------  ----------------
en    English   ru, de, fr, ...
ru    Russian   en, de, fr, ...
```

**Ожидаемый результат:**

1. Выполнен REST-запрос к `/languages`.
2. Пользователь видит список кодов языков и доступных target-языков.
3. История переводов не изменяется.

---

### 9.5. Команда `glossary-add`

**Команда:**

```bash
docstrans glossary-add SOURCE_TERM TARGET_TERM [OPTIONS]
```

**Описание:**  
Добавляет термин в локальный пользовательский глоссарий.

**Аргументы:**

| Аргумент | Тип | Обязательность | Описание |
|---|---:|---:|---|
| `SOURCE_TERM` | `str` | Да | Термин в исходном языке. Пустая строка запрещена. |
| `TARGET_TERM` | `str` | Да | Термин в целевом языке. Пустая строка запрещена. |

**Опции:**

| Опция | Тип | Обязательность | Значение по умолчанию | Описание |
|---|---:|---:|---|---|
| `--source-lang`, `-s` | `str` | Нет | `en` | Язык исходного термина. |
| `--target-lang`, `-t` | `str` | Нет | `ru` | Язык целевого термина. |
| `--case-sensitive` | `bool` | Нет | `False` | Учитывать регистр при применении термина. |
| `--note` | `str` | Нет | `None` | Комментарий к термину. |
| `--replace` | `bool` | Нет | `False` | Обновить существующий термин, если он уже есть. |

**Используемый REST endpoint:**  
Не используется. Команда работает только с локальным SQLite-хранилищем.

**Пример использования:**

```bash
docstrans glossary-add "deployment pipeline" "конвейер развертывания" --source-lang en --target-lang ru
```

**Ожидаемый вывод:**

```text
Glossary term added: deployment pipeline -> конвейер развертывания [en -> ru]
```

**Ожидаемый результат:**

1. В SQLite добавлена запись в таблицу `glossary_terms`.
2. Если термин с такой парой языков уже существует и `--replace` не указан, команда завершается с exit code `6`.
3. Если `--replace` указан, существующая запись обновляется.

---

### 9.6. Команда `glossary-list`

**Команда:**

```bash
docstrans glossary-list [OPTIONS]
```

**Описание:**  
Показывает локальный глоссарий терминов.

**Опции:**

| Опция | Тип | Обязательность | Значение по умолчанию | Описание |
|---|---:|---:|---|---|
| `--source-lang`, `-s` | `str` | Нет | отсутствует | Фильтр по исходному языку. |
| `--target-lang`, `-t` | `str` | Нет | отсутствует | Фильтр по целевому языку. |
| `--search` | `str` | Нет | отсутствует | Поиск по source или target term. |
| `--json` | `bool` | Нет | `False` | Вывести JSON вместо таблицы. |

**Используемый REST endpoint:**  
Не используется. Команда работает только с локальным SQLite-хранилищем.

**Пример использования:**

```bash
docstrans glossary-list --source-lang en --target-lang ru
```

**Ожидаемый табличный вывод:**

```text
ID  Source term          Target term                 Langs    Case sensitive
--  -------------------  --------------------------  -------  --------------
1   deployment pipeline  конвейер развертывания      en->ru   no
```

**Ожидаемый результат:**

1. В консоль выводится таблица терминов.
2. Если терминов нет, выводится `No glossary terms found.` и exit code остается `0`.

---

### 9.7. Команда `glossary-remove`

**Команда:**

```bash
docstrans glossary-remove SOURCE_TERM [OPTIONS]
```

**Описание:**  
Удаляет термин из локального глоссария.

**Аргументы:**

| Аргумент | Тип | Обязательность | Описание |
|---|---:|---:|---|
| `SOURCE_TERM` | `str` | Да | Исходный термин для удаления. |

**Опции:**

| Опция | Тип | Обязательность | Значение по умолчанию | Описание |
|---|---:|---:|---|---|
| `--source-lang`, `-s` | `str` | Нет | `en` | Язык исходного термина. |
| `--target-lang`, `-t` | `str` | Нет | `ru` | Язык целевого термина. |

**Используемый REST endpoint:**  
Не используется. Команда работает только с локальным SQLite-хранилищем.

**Пример использования:**

```bash
docstrans glossary-remove "deployment pipeline" --source-lang en --target-lang ru
```

**Ожидаемый вывод:**

```text
Glossary term removed: deployment pipeline [en -> ru]
```

**Ожидаемый результат:**

1. Термин удален из SQLite.
2. Если термин не найден, команда выводит `Glossary term not found.` и возвращает exit code `4`.

---

### 9.8. Команда `history-list`

**Команда:**

```bash
docstrans history-list [OPTIONS]
```

**Описание:**  
Показывает предыдущие переводы из локальной истории.

**Опции:**

| Опция | Тип | Обязательность | Значение по умолчанию | Описание |
|---|---:|---:|---|---|
| `--limit` | `int` | Нет | `20` | Максимум записей. Минимум `1`, максимум `500`. |
| `--source-lang`, `-s` | `str` | Нет | отсутствует | Фильтр по исходному языку. |
| `--target-lang`, `-t` | `str` | Нет | отсутствует | Фильтр по целевому языку. |
| `--kind` | enum: `text`, `file` | Нет | отсутствует | Фильтр по типу перевода. |
| `--json` | `bool` | Нет | `False` | Вывести JSON вместо таблицы. |

**Используемый REST endpoint:**  
Не используется. Команда работает только с локальным SQLite-хранилищем.

**Пример использования:**

```bash
docstrans history-list --limit 5
```

**Ожидаемый табличный вывод:**

```text
ID  Created at           Kind  Langs    Source preview              Result preview
--  -------------------  ----  -------  --------------------------  --------------------------
7   2026-03-18 13:20:14  text  en->ru   Open the configuration...   Откройте файл конфигурац...
```

**Ожидаемый результат:**

1. В консоль выводится таблица истории.
2. Если записей нет, выводится `No translation history found.` и exit code остается `0`.

---

### 9.9. Команда `export-history`

**Команда:**

```bash
docstrans export-history OUTPUT_PATH [OPTIONS]
```

**Описание:**  
Экспортирует локальную историю переводов в файл.

**Аргументы:**

| Аргумент | Тип | Обязательность | Описание |
|---|---:|---:|---|
| `OUTPUT_PATH` | `Path` | Да | Путь к файлу экспорта. |

**Опции:**

| Опция | Тип | Обязательность | Значение по умолчанию | Описание |
|---|---:|---:|---|---|
| `--format` | enum: `json`, `csv`, `md` | Нет | определяется по расширению или `json` | Формат экспорта. |
| `--limit` | `int` | Нет | отсутствует | Максимум записей. Если не задан, экспортируются все записи. |
| `--source-lang`, `-s` | `str` | Нет | отсутствует | Фильтр по исходному языку. |
| `--target-lang`, `-t` | `str` | Нет | отсутствует | Фильтр по целевому языку. |
| `--overwrite` | `bool` | Нет | `False` | Разрешить перезапись существующего файла. |
| `--create-dirs` | `bool` | Нет | `False` | Создать родительские директории output-файла. |

**Используемый REST endpoint:**  
Не используется. Команда работает только с локальным SQLite-хранилищем.

**Пример использования:**

```bash
docstrans export-history history.json --format json --overwrite
```

**Ожидаемый вывод:**

```text
History exported: history.json
Records exported: 42
```

**Ожидаемый результат:**

1. Создан файл экспорта.
2. Для `json` создается UTF-8 JSON array.
3. Для `csv` создается CSV с заголовком.
4. Для `md` создается Markdown-таблица.
5. Если файл существует и `--overwrite` не указан, команда завершается с exit code `5`.

---

### 9.10. Команда `config-set`

**Команда:**

```bash
docstrans config-set KEY VALUE
```

**Описание:**  
Записывает настройку в локальный config-файл.

**Аргументы:**

| Аргумент | Тип | Обязательность | Допустимые значения | Описание |
|---|---:|---:|---|---|
| `KEY` | enum | Да | `base_url`, `api_key`, `default_source`, `default_target`, `timeout` | Имя настройки. |
| `VALUE` | `str` | Да | зависит от ключа | Значение настройки. |

**Валидация:**

| KEY | Правило VALUE |
|---|---|
| `base_url` | Должен начинаться с `http://` или `https://`; trailing slash удаляется. |
| `api_key` | Непустая строка. |
| `default_source` | Непустой language code или `auto`. |
| `default_target` | Непустой language code, кроме `auto`. |
| `timeout` | Float `> 0` и `<= 300`. |

**Используемый REST endpoint:**  
Не используется. Команда работает только с локальным config-файлом.

**Пример использования:**

```bash
docstrans config-set base_url http://localhost:5000
```

**Ожидаемый вывод:**

```text
Config updated: base_url=http://localhost:5000
```

**Пример с API key:**

```bash
docstrans config-set api_key lt_xxxxxxxxx
```

**Ожидаемый вывод:**

```text
Config updated: api_key=************
```

**Ожидаемый результат:**

1. Создан или обновлен config-файл.
2. API key в консоли всегда маскируется.
3. Config-файл должен быть JSON.

---

### 9.11. Команда `config-show`

**Команда:**

```bash
docstrans config-show [OPTIONS]
```

**Описание:**  
Показывает эффективную конфигурацию: config + env + CLI defaults.

**Опции:**

| Опция | Тип | Обязательность | Значение по умолчанию | Описание |
|---|---:|---:|---|---|
| `--show-secrets` | `bool` | Нет | `False` | Показать API key полностью. По умолчанию ключ маскируется. |
| `--json` | `bool` | Нет | `False` | Вывести JSON вместо таблицы. |

**Используемый REST endpoint:**  
Не используется.

**Пример использования:**

```bash
docstrans config-show
```

**Ожидаемый вывод:**

```text
Key             Value                         Source
--------------  ----------------------------  --------
base_url        https://libretranslate.com     default
api_key         not set                       none
default_source  auto                          default
default_target  ru                            default
timeout         20.0                          default
config_path     /home/user/.config/...        computed
db_path         /home/user/.local/share/...   computed
log_path        /home/user/.local/state/...   computed
```

**Ожидаемый результат:**

1. Пользователь видит текущие настройки.
2. API key скрыт, если не указан `--show-secrets`.

---

### 9.12. Команда `doctor`

**Команда:**

```bash
docstrans doctor [OPTIONS]
```

**Описание:**  
Проверяет локальное окружение: доступность config, SQLite DB, log-директории и REST API.

**Опции:**

| Опция | Тип | Обязательность | Значение по умолчанию | Описание |
|---|---:|---:|---|---|
| `--skip-api` | `bool` | Нет | `False` | Не проверять REST API. |
| `--json` | `bool` | Нет | `False` | Вывести JSON-результат. |

**Используемый REST endpoint:**

```http
GET {base_url}/health
```

Если `/health` недоступен, команда может дополнительно попробовать `GET {base_url}/languages`. Это нужно для совместимости с API-инстансами, где `/health` выключен.

**Пример использования:**

```bash
docstrans doctor
```

**Ожидаемый вывод:**

```text
Config file: ok
Database: ok
Log file: ok
REST API: ok
Base URL: https://libretranslate.com
```

**Ожидаемый результат:**

1. Проверены локальные пути.
2. Проверена возможность подключения к API.
3. Если API недоступен, выводится понятная ошибка и exit code `10`, но локальные проверки все равно отображаются.

## 10. Соответствие команд REST API

| CLI-команда | REST API endpoint | Метод | Использует сеть | Назначение |
|---|---|---:|---:|---|
| `translate-text` | `{base_url}/translate` | `POST` | Да | Перевод строки. |
| `translate-file` | `{base_url}/translate` | `POST` | Да | Перевод сегментов файла. |
| `detect-language` | `{base_url}/detect` | `POST` | Да | Определение языка. |
| `languages-list` | `{base_url}/languages` | `GET` | Да | Список поддерживаемых языков. |
| `doctor` | `{base_url}/health`, fallback `{base_url}/languages` | `GET` | Да, если не `--skip-api` | Проверка доступности API. |
| `glossary-add` | нет | нет | Нет | Локальное SQLite-хранилище. |
| `glossary-list` | нет | нет | Нет | Локальное SQLite-хранилище. |
| `glossary-remove` | нет | нет | Нет | Локальное SQLite-хранилище. |
| `history-list` | нет | нет | Нет | Локальное SQLite-хранилище. |
| `export-history` | нет | нет | Нет | Локальное SQLite-хранилище и файл экспорта. |
| `config-set` | нет | нет | Нет | Локальный config-файл. |
| `config-show` | нет | нет | Нет | Локальный config-файл и env. |

## 11. Локальное хранилище SQLite

### 11.1. Путь по умолчанию

Путь должен вычисляться через `platformdirs`.

Пример для Linux:

```text
~/.local/share/docs-translator-cli/docs-translator.sqlite3
```

Пользователь может переопределить путь:

1. CLI-опцией `--db-path`.
2. Переменной окружения `DOCSTRANS_DB_PATH`.

### 11.2. Инициализация

При первом запуске любой команды CLI должен:

1. Создать директорию для DB, если ее нет.
2. Создать SQLite DB, если ее нет.
3. Применить миграции схемы.

Использовать ручную простую систему миграций через таблицу `schema_migrations`, без Alembic.

### 11.3. Таблицы

#### Таблица `schema_migrations`

```sql
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL
);
```

#### Таблица `glossary_terms`

```sql
CREATE TABLE IF NOT EXISTS glossary_terms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_lang TEXT NOT NULL,
    target_lang TEXT NOT NULL,
    source_term TEXT NOT NULL,
    source_term_norm TEXT NOT NULL,
    target_term TEXT NOT NULL,
    case_sensitive INTEGER NOT NULL DEFAULT 0,
    note TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(source_lang, target_lang, source_term_norm)
);
```

Индексы:

```sql
CREATE INDEX IF NOT EXISTS idx_glossary_langs
ON glossary_terms(source_lang, target_lang);

CREATE INDEX IF NOT EXISTS idx_glossary_search
ON glossary_terms(source_term_norm);
```

#### Таблица `translation_history`

```sql
CREATE TABLE IF NOT EXISTS translation_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    kind TEXT NOT NULL CHECK(kind IN ('text', 'file')),
    provider TEXT NOT NULL,
    base_url TEXT NOT NULL,
    source_lang TEXT NOT NULL,
    target_lang TEXT NOT NULL,
    input_path TEXT,
    output_path TEXT,
    source_text TEXT,
    translated_text TEXT,
    source_hash TEXT NOT NULL,
    translated_hash TEXT NOT NULL,
    glossary_terms_applied INTEGER NOT NULL DEFAULT 0,
    api_status_code INTEGER,
    duration_ms INTEGER NOT NULL
);
```

Индексы:

```sql
CREATE INDEX IF NOT EXISTS idx_history_created_at
ON translation_history(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_history_langs
ON translation_history(source_lang, target_lang);

CREATE INDEX IF NOT EXISTS idx_history_hash
ON translation_history(source_hash, target_lang);
```

### 11.4. Правила хранения истории

1. Для `translate-text` сохранять полный source text и translated text.
2. Для `translate-file` сохранять:
   - `input_path`
   - `output_path`
   - `source_hash`
   - `translated_hash`
   - первые 10000 символов source text
   - первые 10000 символов translated text
3. API key не хранить.
4. При `--no-save` не создавать запись в `translation_history`.
5. `source_hash` и `translated_hash` считать как SHA-256 по UTF-8 тексту.
6. `created_at` хранить в ISO 8601 UTC, например `2026-03-18T10:20:14Z`.

## 12. Конфигурация

### 12.1. Config-файл

Формат: JSON.  
Путь по умолчанию вычисляется через `platformdirs`.

Пример для Linux:

```text
~/.config/docs-translator-cli/config.json
```

Пример файла:

```json
{
  "base_url": "https://libretranslate.com",
  "api_key": null,
  "default_source": "auto",
  "default_target": "ru",
  "timeout": 20.0
}
```

### 12.2. Переменные окружения

| Переменная | Назначение |
|---|---|
| `DOCSTRANS_BASE_URL` | Базовый URL API. |
| `DOCSTRANS_API_KEY` | API key. |
| `DOCSTRANS_DEFAULT_SOURCE` | Исходный язык по умолчанию. |
| `DOCSTRANS_DEFAULT_TARGET` | Целевой язык по умолчанию. |
| `DOCSTRANS_TIMEOUT_SECONDS` | Timeout HTTP-запросов. |
| `DOCSTRANS_DB_PATH` | Путь к SQLite DB. |
| `DOCSTRANS_CONFIG_PATH` | Путь к config-файлу. |
| `DOCSTRANS_LOG_LEVEL` | Уровень логирования: `DEBUG`, `INFO`, `WARNING`, `ERROR`. |

### 12.3. `.env.example`

В репозитории должен быть файл `.env.example`:

```env
DOCSTRANS_BASE_URL=https://libretranslate.com
DOCSTRANS_API_KEY=
DOCSTRANS_DEFAULT_SOURCE=auto
DOCSTRANS_DEFAULT_TARGET=ru
DOCSTRANS_TIMEOUT_SECONDS=20
```

CLI не обязан автоматически читать `.env`. Файл нужен как пример для пользователя и для GitHub-документации. Реальные переменные окружения пользователь экспортирует сам.

### 12.4. Приоритет конфигурации

Приоритет настроек от высокого к низкому:

1. CLI-опция.
2. Переменная окружения.
3. Config-файл.
4. Значение по умолчанию.

## 13. Глоссарий терминов

### 13.1. Цель

Глоссарий нужен для единообразного перевода терминов документации. Например:

```text
deployment pipeline -> конвейер развертывания
pull request -> запрос на слияние
```

### 13.2. Применение глоссария

Перед отправкой текста в API выполнить следующие действия:

1. Получить из SQLite все термины для пары `source_lang -> target_lang`.
2. Если `source_lang=auto`, использовать термины, у которых `source_lang` равен `en`, если target `ru`. Для других target при `auto` использовать все термины с подходящим target, но только если source term найден в тексте.
3. Отсортировать термины по длине `source_term` по убыванию, чтобы длинные термины заменялись раньше коротких.
4. Заменить найденные source terms на placeholder вида:

```text
DTGLOSSARYTOKEN000001
```

5. Отправить текст с placeholder в API.
6. После получения перевода заменить placeholder на `target_term`.
7. Если placeholder не найден в ответе API, выполнить fallback: применить post-processing replacement по наиболее похожему варианту только если это не ломает текст. Также записать warning в лог.

### 13.3. Правила поиска терминов

1. Если `case_sensitive=False`, поиск нечувствителен к регистру.
2. Термин должен матчиться по границам слова для латиницы и кириллицы.
3. Не заменять термин внутри другого слова.
4. Не заменять термины внутри Markdown fenced code blocks, inline code и URL.
5. Один и тот же термин может встречаться много раз; все вхождения должны быть обработаны.

### 13.4. Пример

Глоссарий:

```text
source_lang=en
target_lang=ru
source_term=deployment pipeline
target_term=конвейер развертывания
```

Вход:

```text
Configure the deployment pipeline before release.
```

Перед API:

```text
Configure the DTGLOSSARYTOKEN000001 before release.
```

После API и восстановления:

```text
Настройте конвейер развертывания перед выпуском.
```

## 14. Разбиение файлов на сегменты

### 14.1. Причина

REST API может иметь ограничения по размеру текста. Поэтому `translate-file` должен разбивать файл на сегменты.

### 14.2. Правила сегментации

1. Сегменты не должны превышать `--chunk-size` символов.
2. Сначала делить по пустым строкам.
3. Если абзац длиннее `chunk-size`, делить по предложениям.
4. Если предложение длиннее `chunk-size`, делить по словам.
5. Если одно слово длиннее `chunk-size`, отправлять его отдельным сегментом и логировать warning.
6. Для Markdown code blocks создавать protected-сегменты, которые не отправляются в API.
7. После перевода восстановить исходный порядок всех сегментов.

### 14.3. Пакетная отправка

Если несколько сегментов можно отправить вместе, использовать `q` как JSON array. Максимальное количество сегментов в одном запросе задается `--batch-size`.

## 15. Форматирование вывода

### 15.1. Обычный вывод

1. Успешные короткие результаты печатать в stdout.
2. Ошибки печатать в stderr.
3. Таблицы печатать через Rich `Table`.
4. Для `--json` печатать валидный JSON без Rich-оформления.

### 15.2. Машинно-читаемый JSON

JSON-вывод должен:

1. Использовать UTF-8.
2. Не экранировать кириллицу через `\uXXXX`; использовать `ensure_ascii=False`.
3. Быть валидным JSON.
4. Не содержать цветовых ANSI-кодов.

## 16. Обработка ошибок

### 16.1. Exit codes

| Exit code | Значение |
|---:|---|
| `0` | Успех. |
| `2` | Ошибка CLI-аргументов или валидации Typer/Click. |
| `3` | Ошибка config-файла или некорректная настройка. |
| `4` | Локальные данные не найдены: термин глоссария, запись и т.п. |
| `5` | Ошибка файла: не найден input, output существует без `--overwrite`, нет прав. |
| `6` | Конфликт локальных данных: термин уже существует без `--replace`. |
| `10` | Сетевая ошибка: DNS, connection refused, timeout. |
| `11` | Ошибка авторизации API: HTTP `401` или `403`. |
| `12` | Rate limit API: HTTP `429`. |
| `13` | Некорректный запрос к API: HTTP `400`. |
| `14` | Ошибка сервера API: HTTP `5xx`. |
| `20` | Неожиданная внутренняя ошибка. |

### 16.2. Сетевые ошибки

Обрабатывать исключения HTTPX:

- `httpx.TimeoutException`
- `httpx.ConnectError`
- `httpx.NetworkError`
- `httpx.HTTPStatusError`
- общий `httpx.HTTPError`

Пользовательский вывод должен быть коротким:

```text
Error: translation API timeout after 20.0 seconds.
```

Детали с URL без API key записывать в log-файл.

### 16.3. Ошибки API

| HTTP status | Поведение |
|---:|---|
| `400` | Вывести `Error: invalid translation API request.` Exit code `13`. |
| `401`/`403` | Вывести `Error: API key is missing or invalid.` Exit code `11`. |
| `429` | Вывести `Error: API rate limit exceeded.` Exit code `12`. |
| `500-599` | Вывести `Error: translation API server error.` Exit code `14`. |

Если тело ответа содержит JSON `{ "error": "..." }`, коротко добавить сообщение API:

```text
Error: API rate limit exceeded: Slow down
```

### 16.4. Ошибки файлов

1. Если input-файл не существует: exit code `5`.
2. Если input-путь является директорией: exit code `5`.
3. Если output существует без `--overwrite`: exit code `5`.
4. Если кодировка неверная: exit code `5`, сообщение `Error: cannot decode file as utf-8.`.
5. Если нет прав на запись: exit code `5`.

### 16.5. Ошибки config

1. Некорректный JSON config-файл: exit code `3`.
2. Некорректный `base_url`: exit code `3`.
3. Некорректный `timeout`: exit code `3`.
4. API key в config может быть `null` или непустой строкой.

## 17. Логирование

### 17.1. Путь к логам

Путь вычисляется через `platformdirs`.

Пример для Linux:

```text
~/.local/state/docs-translator-cli/docs-translator.log
```

### 17.2. Формат логов

Использовать стандартный Python `logging` и `RotatingFileHandler`.

Параметры:

- `maxBytes=1_048_576`
- `backupCount=3`
- `encoding="utf-8"`

Формат строки:

```text
2026-03-18T10:20:14Z INFO docstrans.api Translation request completed status=200 duration_ms=512
```

### 17.3. Что логировать

Логировать:

1. Старт команды без полного source text.
2. API endpoint path без API key.
3. HTTP status code.
4. Duration ms.
5. Ошибки и stack trace при `--verbose` или DEBUG log level.
6. Путь к input/output файлам.
7. Количество сегментов и примененных glossary terms.

Не логировать:

1. API key.
2. Полный текст пользовательских документов.
3. Полные переводы больших файлов.
4. Значения переменных окружения целиком.

## 18. Структура проекта

Исполнитель должен создать следующую структуру:

```text
docs-translator-cli/
├── .env.example
├── .gitignore
├── .python-version
├── LICENSE
├── README.md
├── pyproject.toml
├── uv.lock
├── src/
│   └── docstrans/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py
│       ├── config.py
│       ├── constants.py
│       ├── exceptions.py
│       ├── logging_setup.py
│       ├── paths.py
│       ├── api/
│       │   ├── __init__.py
│       │   ├── client.py
│       │   └── models.py
│       ├── db/
│       │   ├── __init__.py
│       │   ├── connection.py
│       │   ├── migrations.py
│       │   ├── glossary_repo.py
│       │   └── history_repo.py
│       ├── services/
│       │   ├── __init__.py
│       │   ├── detection_service.py
│       │   ├── export_service.py
│       │   ├── file_service.py
│       │   ├── glossary_service.py
│       │   ├── history_service.py
│       │   ├── markdown_protection.py
│       │   ├── segmentation.py
│       │   └── translation_service.py
│       └── ui/
│           ├── __init__.py
│           └── output.py
└── tests/
    ├── conftest.py
    ├── test_api_client.py
    ├── test_cli_translate_text.py
    ├── test_config.py
    ├── test_file_translation.py
    ├── test_glossary.py
    ├── test_history_export.py
    ├── test_markdown_protection.py
    └── test_segmentation.py
```

## 19. `pyproject.toml`

Минимальная конфигурация:

```toml
[project]
name = "docs-translator-cli"
version = "0.1.0"
description = "CLI tool for translating documentation files using a REST translation API, SQLite history, and a local glossary."
readme = "README.md"
requires-python = ">=3.12,<3.13"
license = { text = "MIT" }
authors = [
  { name = "Student" }
]
dependencies = [
  "typer>=0.24,<1.0",
  "rich>=14,<16",
  "httpx>=0.27,<1.0",
  "platformdirs>=4,<5"
]

[project.scripts]
docstrans = "docstrans.cli:app"

[dependency-groups]
dev = [
  "pytest>=8,<10",
  "pytest-cov>=5,<8",
  "respx>=0.21,<1.0",
  "ruff>=0.8,<1.0"
]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "SIM"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--cov=docstrans --cov-report=term-missing"
```

`.python-version`:

```text
3.12
```

## 20. Установка и запуск

README должен содержать эти команды.

### 20.1. Создание проекта

```bash
uv sync
```

### 20.2. Запуск CLI

```bash
uv run docstrans --help
```

### 20.3. Проверка окружения

```bash
uv run docstrans doctor
```

### 20.4. Пример перевода

```bash
uv run docstrans translate-text "Hello world" --source en --target ru
```

### 20.5. Тесты

```bash
uv run pytest
```

### 20.6. Линтинг и форматирование

```bash
uv run ruff check .
uv run ruff format --check .
```

## 21. README.md

README должен содержать:

1. Краткое описание проекта.
2. Список возможностей.
3. Требования: Python 3.12, uv.
4. Установку через `uv sync`.
5. Конфигурацию API key и base URL.
6. Таблицу команд.
7. Примеры каждой команды.
8. Описание REST API endpoints.
9. Описание SQLite-хранилища.
10. Инструкцию по тестированию.
11. Инструкцию по запуску LibreTranslate локально, если публичный API недоступен:

```bash
docker run -it --rm -p 5000:5000 libretranslate/libretranslate
```

После этого:

```bash
docstrans config-set base_url http://localhost:5000
```

12. Раздел с типичными ошибками и их исправлением.

## 22. Тестирование

### 22.1. Общие требования

1. Все тесты должны запускаться командой:

```bash
uv run pytest
```

2. Тесты не должны выполнять реальные сетевые запросы.
3. Все HTTP-вызовы должны мокироваться через RESPX или через внедрение fake client.
4. Покрытие кода должно быть не ниже `70%`.
5. Тесты должны использовать временные директории `tmp_path` для config, DB и output-файлов.

### 22.2. Минимальный набор тестов

Нужно реализовать не менее 12 тестов:

1. `test_translate_text_calls_translate_endpoint`  
   Проверить, что `translate-text` отправляет `POST /translate` с корректными `q`, `source`, `target`, `format`.

2. `test_translate_text_saves_history`  
   Проверить, что после успешного перевода появляется запись в `translation_history`.

3. `test_translate_text_no_save`  
   Проверить, что с `--no-save` история не изменяется.

4. `test_detect_language_calls_detect_endpoint`  
   Проверить, что `detect-language` отправляет `POST /detect` и выводит лучший язык.

5. `test_languages_list_calls_languages_endpoint`  
   Проверить, что `languages-list` вызывает `GET /languages` и печатает таблицу или JSON.

6. `test_glossary_add_list_remove`  
   Проверить полный CRUD глоссария.

7. `test_glossary_duplicate_without_replace_fails`  
   Проверить, что дубликат без `--replace` дает exit code `6`.

8. `test_glossary_replaces_longest_term_first`  
   Проверить, что `deployment pipeline` применяется раньше `deployment`.

9. `test_translate_file_creates_default_output`  
   Проверить, что `README.md` переводится в `README.ru.md`.

10. `test_translate_file_refuses_overwrite_without_flag`  
    Проверить защиту от перезаписи.

11. `test_markdown_code_blocks_are_not_translated`  
    Проверить, что fenced code block и inline code не отправляются в API и сохраняются без изменений.

12. `test_export_history_json_csv_md`  
    Проверить экспорт истории во все три формата.

13. `test_config_env_has_priority_over_file`  
    Проверить приоритет env над config-файлом.

14. `test_api_429_maps_to_exit_code_12`  
    Проверить обработку rate limit.

15. `test_timeout_maps_to_exit_code_10`  
    Проверить обработку timeout.

Допускается реализовать больше тестов.

## 23. Критерии приемки

Проект считается готовым, если выполняются все пункты:

1. Команда `uv sync` завершается успешно.
2. Команда `uv run docstrans --help` показывает список всех команд.
3. Реализованы все команды из раздела 8.
4. Команды перевода и определения языка используют REST API.
5. Локальные команды работают через SQLite/config-файл.
6. `uv run pytest` проходит без ошибок.
7. `uv run ruff check .` проходит без ошибок.
8. `uv run ruff format --check .` проходит без ошибок.
9. Нет реальных HTTP-запросов в тестах.
10. README содержит установку, настройку, команды, REST API endpoints и тестирование.
11. API key нигде не выводится полностью, кроме `config-show --show-secrets`.
12. Большие файлы не ломают CLI и обрабатываются через сегментацию.
13. Markdown code blocks не переводятся при `--preserve-markdown-code=True`.
14. История и глоссарий сохраняются между запусками.
15. Ошибки сети, API, файлов и config обрабатываются понятными сообщениями и корректными exit codes.

## 24. Запрещенные решения

Исполнитель не должен:

1. Хардкодить API key.
2. Использовать реальные сетевые запросы в тестах.
3. Игнорировать REST API и делать mock-перевод в рабочем коде.
4. Сохранять API key в лог.
5. Делать GUI.
6. Добавлять ненужные тяжелые зависимости: pandas, numpy, FastAPI, Django, SQLAlchemy.
7. Использовать нестандартную структуру проекта без `src/` layout.
8. Хранить SQLite DB внутри репозитория по умолчанию.
9. Перезаписывать пользовательские файлы без `--overwrite`.
10. Печатать traceback обычному пользователю без `--verbose`.

## 25. Пример полного сценария использования

```bash
# 1. Проверить окружение
uv run docstrans doctor

# 2. Настроить локальный LibreTranslate
uv run docstrans config-set base_url http://localhost:5000

# 3. Добавить термин
uv run docstrans glossary-add "deployment pipeline" "конвейер развертывания" --source-lang en --target-lang ru

# 4. Перевести строку
uv run docstrans translate-text "Configure the deployment pipeline" --source en --target ru

# 5. Перевести файл
uv run docstrans translate-file README.md --source en --target ru

# 6. Посмотреть историю
uv run docstrans history-list --limit 10

# 7. Экспортировать историю
uv run docstrans export-history history.md --format md --overwrite
```

## 26. Ожидаемый результат от исполнителя

Исполнитель должен вернуть архив или репозиторий со следующим содержимым:

1. Полный исходный код проекта.
2. `pyproject.toml` с корректными зависимостями и entry point `docstrans`.
3. `uv.lock`.
4. `README.md`.
5. `.env.example`.
6. `.gitignore`.
7. `LICENSE`.
8. Папка `tests/` с unit-тестами.
9. Рабочая CLI-команда `docstrans`.
10. Отсутствие лишних временных файлов, SQLite DB, cache и логов в репозитории.

## 27. Финальная проверка команд

После получения проекта нужно выполнить:

```bash
uv sync
uv run docstrans --help
uv run docstrans config-show
uv run docstrans doctor --skip-api
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

Для проверки REST API с локальным LibreTranslate:

```bash
docker run -it --rm -p 5000:5000 libretranslate/libretranslate
uv run docstrans --base-url http://localhost:5000 doctor
uv run docstrans --base-url http://localhost:5000 translate-text "Hello world" --source en --target es
```

Если все команды проходят, проект соответствует ТЗ.
