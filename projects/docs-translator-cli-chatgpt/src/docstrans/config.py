from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from docstrans import constants
from docstrans.exceptions import ConfigError
from docstrans.paths import default_config_path, default_db_path, default_log_path

_ALLOWED_CONFIG_KEYS = {"base_url", "api_key", "default_source", "default_target", "timeout"}


@dataclass(frozen=True)
class EffectiveConfig:
    base_url: str
    api_key: str | None
    default_source: str
    default_target: str
    timeout: float
    config_path: Path
    db_path: Path
    log_path: Path
    sources: dict[str, str] = field(default_factory=dict)


def mask_secret(value: str | None) -> str:
    if not value:
        return "not set"
    return "*" * 12


def normalize_base_url(value: str) -> str:
    value = value.strip().rstrip("/")
    if not value.startswith(("http://", "https://")):
        raise ConfigError("Error: base_url must start with http:// or https://.")
    return value


def validate_timeout(value: Any, *, max_value: float = 300.0) -> float:
    try:
        timeout = float(value)
    except (TypeError, ValueError) as exc:
        raise ConfigError("Error: timeout must be a number.") from exc
    if timeout <= 0 or timeout > max_value:
        raise ConfigError("Error: timeout must be > 0 and <= 300.")
    return timeout


def validate_language_code(value: str, *, allow_auto: bool) -> str:
    value = value.strip()
    if not value:
        raise ConfigError("Error: language code cannot be empty.")
    if value == "auto" and not allow_auto:
        raise ConfigError("Error: target language cannot be auto.")
    return value


def load_config_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Error: invalid config JSON: {path}") from exc
    if not isinstance(data, dict):
        raise ConfigError("Error: config file must contain a JSON object.")
    unknown = set(data) - _ALLOWED_CONFIG_KEYS
    if unknown:
        raise ConfigError(f"Error: unknown config keys: {', '.join(sorted(unknown))}.")
    return data


def _get_value(
    key: str,
    env_name: str,
    config_data: dict[str, Any],
    default: Any,
    cli_value: Any | None = None,
) -> tuple[Any, str]:
    if cli_value is not None:
        return cli_value, "cli"
    env_value = os.getenv(env_name)
    if env_value not in (None, ""):
        return env_value, "env"
    if key in config_data and config_data[key] not in (None, ""):
        return config_data[key], "config"
    return default, "default"


def build_config(
    *,
    config_path: Path | None = None,
    db_path: Path | None = None,
    base_url: str | None = None,
    api_key: str | None = None,
    timeout: float | None = None,
) -> EffectiveConfig:
    resolved_config_path = Path(
        config_path or os.getenv("DOCSTRANS_CONFIG_PATH") or default_config_path()
    )
    resolved_db_path = Path(db_path or os.getenv("DOCSTRANS_DB_PATH") or default_db_path())
    resolved_log_path = default_log_path()
    config_data = load_config_file(resolved_config_path)

    sources: dict[str, str] = {}

    raw_base_url, sources["base_url"] = _get_value(
        "base_url", "DOCSTRANS_BASE_URL", config_data, constants.DEFAULT_BASE_URL, base_url
    )
    raw_api_key, sources["api_key"] = _get_value(
        "api_key", "DOCSTRANS_API_KEY", config_data, None, api_key
    )
    raw_default_source, sources["default_source"] = _get_value(
        "default_source",
        "DOCSTRANS_DEFAULT_SOURCE",
        config_data,
        constants.DEFAULT_SOURCE,
    )
    raw_default_target, sources["default_target"] = _get_value(
        "default_target",
        "DOCSTRANS_DEFAULT_TARGET",
        config_data,
        constants.DEFAULT_TARGET,
    )
    raw_timeout, sources["timeout"] = _get_value(
        "timeout", "DOCSTRANS_TIMEOUT_SECONDS", config_data, constants.DEFAULT_TIMEOUT, timeout
    )

    return EffectiveConfig(
        base_url=normalize_base_url(str(raw_base_url)),
        api_key=str(raw_api_key) if raw_api_key not in (None, "") else None,
        default_source=validate_language_code(str(raw_default_source), allow_auto=True),
        default_target=validate_language_code(str(raw_default_target), allow_auto=False),
        timeout=validate_timeout(raw_timeout),
        config_path=resolved_config_path,
        db_path=resolved_db_path,
        log_path=resolved_log_path,
        sources=sources,
    )


def write_config_value(path: Path, key: str, value: str) -> tuple[str, Any]:
    if key not in _ALLOWED_CONFIG_KEYS:
        allowed = ", ".join(sorted(_ALLOWED_CONFIG_KEYS))
        raise ConfigError(f"Error: config key must be one of: {allowed}.")

    data = load_config_file(path)
    if key == "base_url":
        validated: Any = normalize_base_url(value)
    elif key == "api_key":
        if not value.strip():
            raise ConfigError("Error: api_key cannot be empty.")
        validated = value.strip()
    elif key == "default_source":
        validated = validate_language_code(value, allow_auto=True)
    elif key == "default_target":
        validated = validate_language_code(value, allow_auto=False)
    elif key == "timeout":
        validated = validate_timeout(value)
    else:
        raise ConfigError("Error: unsupported config key.")

    path.parent.mkdir(parents=True, exist_ok=True)
    data[key] = validated
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return key, validated
