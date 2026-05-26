"""Configuration loading with priority: CLI > env > config file > defaults."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from docstrans.constants import (
    DEFAULT_BASE_URL,
    DEFAULT_SOURCE_LANG,
    DEFAULT_TARGET_LANG,
    DEFAULT_TIMEOUT,
)
from docstrans.exceptions import ConfigError
from docstrans.paths import default_config_path, default_db_path, default_log_path


@dataclass
class AppConfig:
    base_url: str = DEFAULT_BASE_URL
    api_key: str | None = None
    default_source: str = DEFAULT_SOURCE_LANG
    default_target: str = DEFAULT_TARGET_LANG
    timeout: float = DEFAULT_TIMEOUT
    config_path: Path = field(default_factory=default_config_path)
    db_path: Path = field(default_factory=default_db_path)
    log_path: Path = field(default_factory=default_log_path)

    # Track the source of each value (for config-show)
    _sources: dict[str, str] = field(default_factory=dict, repr=False)

    def mask_api_key(self) -> str:
        if not self.api_key:
            return "not set"
        return "************"


def _strip_url(url: str) -> str:
    return url.rstrip("/")


def _validate_base_url(value: str) -> str:
    v = _strip_url(value)
    if not (v.startswith("http://") or v.startswith("https://")):
        raise ConfigError(f"base_url must start with http:// or https://, got: {value!r}")
    return v


def _validate_timeout(value: Any) -> float:
    try:
        t = float(value)
    except (TypeError, ValueError) as e:
        raise ConfigError(f"timeout must be a number, got: {value!r}") from e
    if t <= 0 or t > 300:
        raise ConfigError(f"timeout must be > 0 and <= 300, got: {t}")
    return t


def _load_file(path: Path) -> dict[str, Any]:
    """Load and parse config JSON file. Returns {} if file doesn't exist."""
    if not path.exists():
        return {}
    try:
        text = path.read_text(encoding="utf-8")
        data = json.loads(text)
        if not isinstance(data, dict):
            raise ConfigError(f"Config file is not a JSON object: {path}")
        return data
    except json.JSONDecodeError as e:
        raise ConfigError(f"Config file contains invalid JSON: {path}: {e}") from e


def load_config(
    config_path: Path | None = None,
    db_path: Path | None = None,
    base_url: str | None = None,
    api_key: str | None = None,
    timeout: float | None = None,
) -> AppConfig:
    """Build AppConfig from file + env + explicit overrides."""
    resolved_config_path = (
        config_path or _env_path("DOCSTRANS_CONFIG_PATH") or default_config_path()
    )
    resolved_db_path = db_path or _env_path("DOCSTRANS_DB_PATH") or default_db_path()

    file_data = _load_file(resolved_config_path)

    cfg = AppConfig(
        config_path=resolved_config_path,
        db_path=resolved_db_path,
        log_path=default_log_path(),
    )
    sources: dict[str, str] = {}

    # base_url
    if base_url is not None:
        cfg.base_url = _validate_base_url(base_url)
        sources["base_url"] = "cli"
    elif env_url := os.environ.get("DOCSTRANS_BASE_URL"):
        cfg.base_url = _validate_base_url(env_url)
        sources["base_url"] = "env"
    elif "base_url" in file_data:
        cfg.base_url = _validate_base_url(str(file_data["base_url"]))
        sources["base_url"] = "file"
    else:
        sources["base_url"] = "default"

    # api_key
    if api_key is not None:
        cfg.api_key = api_key
        sources["api_key"] = "cli"
    elif env_key := os.environ.get("DOCSTRANS_API_KEY"):
        cfg.api_key = env_key
        sources["api_key"] = "env"
    elif file_data.get("api_key"):
        cfg.api_key = str(file_data["api_key"])
        sources["api_key"] = "file"
    else:
        cfg.api_key = None
        sources["api_key"] = "none"

    # default_source
    if env_src := os.environ.get("DOCSTRANS_DEFAULT_SOURCE"):
        cfg.default_source = env_src
        sources["default_source"] = "env"
    elif "default_source" in file_data:
        cfg.default_source = str(file_data["default_source"])
        sources["default_source"] = "file"
    else:
        sources["default_source"] = "default"

    # default_target
    if env_tgt := os.environ.get("DOCSTRANS_DEFAULT_TARGET"):
        cfg.default_target = env_tgt
        sources["default_target"] = "env"
    elif "default_target" in file_data:
        cfg.default_target = str(file_data["default_target"])
        sources["default_target"] = "file"
    else:
        sources["default_target"] = "default"

    # timeout
    if timeout is not None:
        cfg.timeout = _validate_timeout(timeout)
        sources["timeout"] = "cli"
    elif env_to := os.environ.get("DOCSTRANS_TIMEOUT_SECONDS"):
        cfg.timeout = _validate_timeout(env_to)
        sources["timeout"] = "env"
    elif "timeout" in file_data:
        cfg.timeout = _validate_timeout(file_data["timeout"])
        sources["timeout"] = "file"
    else:
        sources["timeout"] = "default"

    cfg._sources = sources
    return cfg


def _env_path(name: str) -> Path | None:
    val = os.environ.get(name)
    return Path(val) if val else None


def write_config_key(config_path: Path, key: str, value: Any) -> None:
    """Update a single key in the config JSON file."""
    data: dict[str, Any] = {}
    if config_path.exists():
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = {}
    config_path.parent.mkdir(parents=True, exist_ok=True)
    data[key] = value
    config_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
