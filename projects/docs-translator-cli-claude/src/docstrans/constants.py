"""Application-wide constants."""

APP_NAME = "docs-translator-cli"
APP_DIR_NAME = "docs-translator-cli"

DEFAULT_BASE_URL = "https://libretranslate.com"
DEFAULT_SOURCE_LANG = "auto"
DEFAULT_TARGET_LANG = "ru"
DEFAULT_TIMEOUT = 20.0
DEFAULT_CHUNK_SIZE = 4000
DEFAULT_BATCH_SIZE = 20

DB_FILENAME = "docs-translator.sqlite3"
CONFIG_FILENAME = "config.json"
LOG_FILENAME = "docs-translator.log"

GLOSSARY_TOKEN_PREFIX = "DTGLOSSARYTOKEN"

SUPPORTED_EXTENSIONS = {".txt", ".md", ".rst"}

CONFIG_KEYS = ("base_url", "api_key", "default_source", "default_target", "timeout")

EXIT_OK = 0
EXIT_ARGS = 2
EXIT_CONFIG = 3
EXIT_NOT_FOUND = 4
EXIT_FILE = 5
EXIT_CONFLICT = 6
EXIT_NETWORK = 10
EXIT_AUTH = 11
EXIT_RATE_LIMIT = 12
EXIT_BAD_REQUEST = 13
EXIT_SERVER = 14
EXIT_INTERNAL = 20

LOG_MAX_BYTES = 1_048_576
LOG_BACKUP_COUNT = 3
