# Docs Translator CLI

Docs Translator CLI is a Python 3.12 command-line utility for translating documentation files and short text strings through a LibreTranslate-compatible REST API. It stores translation history and a user glossary in SQLite.

## Features

- Translate a text string through `POST /translate`.
- Translate `.txt`, `.md`, and `.rst` files through `POST /translate`.
- Detect language through `POST /detect`.
- List supported languages through `GET /languages`.
- Check local environment and API through `GET /health` with `/languages` fallback.
- Maintain a local SQLite glossary.
- Apply glossary terms before API translation through placeholders.
- Store translation history in SQLite.
- Export history to JSON, CSV, or Markdown.
- Configure base URL, API key, default languages, and timeout.
- Run unit tests without real HTTP requests.

## Requirements

- Python 3.12
- uv

## Installation

```bash
uv sync
```

## CLI help

```bash
uv run docstrans --help
```

Global options must be placed before the command:

```bash
docstrans [GLOBAL_OPTIONS] COMMAND [COMMAND_OPTIONS]
```

Important global options:

```bash
--config-path PATH
--db-path PATH
--base-url URL
--api-key TEXT
--timeout FLOAT
--verbose
--no-color
```

## Configuration

Configuration is resolved in this order:

1. CLI option.
2. Environment variable.
3. JSON config file.
4. Default value.

Default config file is computed with `platformdirs`, for example:

```text
~/.config/docs-translator-cli/config.json
```

Default SQLite database path is computed with `platformdirs`, for example:

```text
~/.local/share/docs-translator-cli/docs-translator.sqlite3
```

Supported environment variables:

| Variable | Purpose |
|---|---|
| `DOCSTRANS_BASE_URL` | LibreTranslate-compatible API base URL. |
| `DOCSTRANS_API_KEY` | API key. |
| `DOCSTRANS_DEFAULT_SOURCE` | Default source language. |
| `DOCSTRANS_DEFAULT_TARGET` | Default target language. |
| `DOCSTRANS_TIMEOUT_SECONDS` | HTTP timeout in seconds. |
| `DOCSTRANS_DB_PATH` | SQLite database path. |
| `DOCSTRANS_CONFIG_PATH` | Config file path. |
| `DOCSTRANS_LOG_LEVEL` | Logging level. |

Set local LibreTranslate:

```bash
uv run docstrans config-set base_url http://localhost:5000
```

Set API key:

```bash
uv run docstrans config-set api_key lt_xxxxxxxxx
```

Show effective config:

```bash
uv run docstrans config-show
uv run docstrans config-show --json
uv run docstrans config-show --show-secrets
```

## Running LibreTranslate locally

If the public API is unavailable or requires an API key, run a local LibreTranslate instance:

```bash
docker run -it --rm -p 5000:5000 libretranslate/libretranslate
```

Then configure the CLI:

```bash
uv run docstrans config-set base_url http://localhost:5000
```

## Commands

| Command | REST endpoint | Purpose |
|---|---|---|
| `translate-text` | `POST /translate` | Translate one string. |
| `translate-file` | `POST /translate` | Translate documentation files. |
| `detect-language` | `POST /detect` | Detect text language. |
| `languages-list` | `GET /languages` | List supported API languages. |
| `doctor` | `GET /health`, fallback `GET /languages` | Check local environment and API. |
| `glossary-add` | none | Add a local glossary term. |
| `glossary-list` | none | List local glossary terms. |
| `glossary-remove` | none | Remove a glossary term. |
| `history-list` | none | List translation history. |
| `export-history` | none | Export translation history. |
| `config-set` | none | Save config value. |
| `config-show` | none | Show effective config. |

## Examples

### Check environment

```bash
uv run docstrans doctor
uv run docstrans doctor --skip-api
uv run docstrans doctor --json --skip-api
```

### Translate text

```bash
uv run docstrans translate-text "Open the configuration file" --source en --target ru
uv run docstrans translate-text "Open the configuration file" --source en --target ru --json
uv run docstrans translate-text "Hello" --source en --target es --output hello.es.txt
uv run docstrans translate-text "Hello" --source en --target es --no-save
```

Expected normal output is only the translated text. JSON output contains `source_language`, `target_language`, `translated_text`, `provider`, and `saved_to_history`.

### Translate file

```bash
uv run docstrans translate-file README.md --source en --target ru
uv run docstrans translate-file README.md --source en --target ru --output README.ru.md --overwrite
uv run docstrans translate-file docs/install.txt --source en --target de --create-dirs
uv run docstrans translate-file README.md --source en --target ru --json
```

If `--output` is omitted, output is generated beside the input file:

| Input | Target | Output |
|---|---|---|
| `README.md` | `ru` | `README.ru.md` |
| `docs/install.txt` | `en` | `docs/install.en.txt` |

Markdown fenced code blocks, inline code, and URLs are protected by default.

### Detect language

```bash
uv run docstrans detect-language "Bonjour tout le monde"
uv run docstrans detect-language "Bonjour tout le monde" --json
```

### List API languages

```bash
uv run docstrans languages-list
uv run docstrans languages-list --json
uv run docstrans languages-list --target-for en
```

### Glossary

```bash
uv run docstrans glossary-add "deployment pipeline" "конвейер развертывания" --source-lang en --target-lang ru
uv run docstrans glossary-add "pull request" "запрос на слияние" --source-lang en --target-lang ru --note "Git term"
uv run docstrans glossary-list --source-lang en --target-lang ru
uv run docstrans glossary-list --search deployment --json
uv run docstrans glossary-remove "deployment pipeline" --source-lang en --target-lang ru
```

Duplicate glossary terms fail unless `--replace` is used.

### History

```bash
uv run docstrans history-list --limit 10
uv run docstrans history-list --kind text --json
uv run docstrans export-history history.json --format json --overwrite
uv run docstrans export-history history.csv --format csv --overwrite
uv run docstrans export-history history.md --format md --overwrite
```

## REST API details

The utility supports LibreTranslate-compatible APIs.

### `POST /translate`

Request for one string:

```json
{
  "q": "Hello world",
  "source": "en",
  "target": "ru",
  "format": "text",
  "api_key": "only if configured"
}
```

Request for file segments:

```json
{
  "q": ["First paragraph", "Second paragraph"],
  "source": "en",
  "target": "ru",
  "format": "text",
  "api_key": "only if configured"
}
```

Expected response:

```json
{"translatedText": "Привет, мир"}
```

or:

```json
{"translatedText": ["Первый абзац", "Второй абзац"]}
```

### `POST /detect`

```json
{"q": "Bonjour", "api_key": "only if configured"}
```

Expected response:

```json
[{"confidence": 90.0, "language": "fr"}]
```

### `GET /languages`

Expected response:

```json
[{"code": "en", "name": "English", "targets": ["ru", "de", "fr"]}]
```

### `GET /health`

Expected response:

```json
{"status": "ok"}
```

## SQLite storage

SQLite is initialized automatically on first CLI startup. The schema uses simple migrations through `schema_migrations`.

Tables:

- `schema_migrations`
- `glossary_terms`
- `translation_history`

The glossary stores source and target terms with language pair and case-sensitivity flag. Translation history stores translation kind, provider, base URL, languages, optional file paths, text previews, SHA-256 hashes, API status code, and duration.

API keys are never stored in SQLite.

## Logging

Logs are written through `RotatingFileHandler` with:

- `maxBytes=1048576`
- `backupCount=3`
- UTF-8 encoding

Default path is computed with `platformdirs`, for example:

```text
~/.local/state/docs-translator-cli/docs-translator.log
```

API keys are masked in output and not written to logs.

## Exit codes

| Code | Meaning |
|---:|---|
| 0 | Success. |
| 2 | CLI validation error. |
| 3 | Config error. |
| 4 | Local data not found. |
| 5 | File error. |
| 6 | Local data conflict. |
| 10 | Network error or timeout. |
| 11 | API authorization error. |
| 12 | API rate limit. |
| 13 | Invalid API request. |
| 14 | API server error. |
| 20 | Unexpected internal error. |

## Typical errors

### Public LibreTranslate requires an API key

Use a self-hosted LibreTranslate instance or set an API key:

```bash
uv run docstrans config-set api_key lt_xxxxxxxxx
```

### API unavailable

Check the endpoint:

```bash
uv run docstrans doctor
```

Use local Docker instance:

```bash
docker run -it --rm -p 5000:5000 libretranslate/libretranslate
uv run docstrans config-set base_url http://localhost:5000
```

### Output file already exists

Use a different path or explicitly allow overwrite:

```bash
uv run docstrans translate-file README.md --target ru --overwrite
```

### Wrong config JSON

Open the config path shown by:

```bash
uv run docstrans config-show
```

Fix JSON syntax or delete the file to recreate it.

## Testing

```bash
uv run pytest
```

Tests use temporary paths and mocked/fake HTTP clients. They do not perform real network requests.

## Linting and formatting

```bash
uv run ruff check .
uv run ruff format --check .
```

## Final verification

```bash
uv sync
uv run docstrans --help
uv run docstrans config-show
uv run docstrans doctor --skip-api
uv run pytest
uv run ruff check .
uv run ruff format --check .
```
