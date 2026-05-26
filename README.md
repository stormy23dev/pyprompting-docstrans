# Docs Translator CLI: сравнение ChatGPT и Claude

![Python](https://img.shields.io/badge/python-3.12-blue)
![uv](https://img.shields.io/badge/package%20manager-uv-purple)
![Tests](https://img.shields.io/badge/tests-ChatGPT%2022%20%7C%20Claude%2045-brightgreen)
![Coverage](https://img.shields.io/badge/coverage-80%25%20%7C%2069%25-brightgreen)
![Ruff](https://img.shields.io/badge/ruff-passed-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)

Практическая работа по разработке CLI-утилиты с использованием ИИ-инструментов. В репозитории сравниваются две независимые реализации проекта **Docs Translator CLI**, созданные с помощью ChatGPT и Claude по одному техническому заданию.

## Проект

Docs Translator CLI — консольная Python-утилита для перевода текстовых файлов документации и отдельных строк через LibreTranslate-compatible REST API. Проект использует SQLite для локальной истории переводов и пользовательского глоссария терминов.

## Структура репозитория

```text
.
├── version1/              # реализация ChatGPT
├── version2/              # реализация Claude
├── docs/                  # ТЗ, отчёт, промпты, логи
├── tests/                 # дополнительные материалы по тестированию
├── screenshots/           # скриншоты работы CLI
├── README.md
├── comparison.md
├── LICENSE
└── .gitignore
```

## Быстрый запуск

```bash
cd version1/docs-translator-cli-chatgpt
uv sync
uv run docstrans --help
uv run pytest
uv run ruff check .
```

```bash
cd version2/docs-translator-cli-claude
uv sync
uv run docstrans --help
uv run pytest
uv run ruff check .
```

## REST API

Для проверки без платного внешнего ключа можно поднять LibreTranslate локально:

```bash
docker run -it --rm -p 5000:5000 libretranslate/libretranslate
```

Затем настроить CLI:

```bash
uv run docstrans config-set base_url http://localhost:5000
uv run docstrans doctor
```

Используемые endpoints:

| Команда | Endpoint |
|---|---|
| `translate-text` | `POST /translate` |
| `translate-file` | `POST /translate` |
| `detect-language` | `POST /detect` |
| `languages-list` | `GET /languages` |
| `doctor` | `GET /health`, fallback `GET /languages` |

## Итоги проверки

| Версия | Тесты | Coverage | Ruff | Команд CLI |
|---|---:|---:|---:|---:|
| ChatGPT | 22 passed | 80% | passed после исправления SIM105 | 12 |
| Claude | 45 passed | 69% | passed | 12 |

## Документация

- `docs/docs_translator_cli_tz.md` — техническое задание.
- `docs/report.md` — полный отчёт.
- `comparison.md` — сравнительный анализ ChatGPT и Claude.
- `docs/prompts_chatgpt.md` — промпты и ответы ChatGPT.
- `docs/prompts_claude.md` — промпты и ответы Claude.
