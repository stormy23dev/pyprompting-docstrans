"""Tests for config loading priority."""

from __future__ import annotations

import json

import pytest

from docstrans.config import load_config
from docstrans.exceptions import ConfigError


def test_config_defaults(tmp_path):
    cfg = load_config(config_path=tmp_path / "nonexistent.json")
    assert cfg.base_url == "https://libretranslate.com"
    assert cfg.default_target == "ru"
    assert cfg.timeout == 20.0
    assert cfg.api_key is None


def test_config_file_is_read(tmp_path):
    cfg_file = tmp_path / "config.json"
    data = {"base_url": "http://local:5000", "default_target": "de"}
    cfg_file.write_text(json.dumps(data), encoding="utf-8")
    cfg = load_config(config_path=cfg_file)
    assert cfg.base_url == "http://local:5000"
    assert cfg.default_target == "de"


# test_config_env_has_priority_over_file
def test_config_env_has_priority_over_file(tmp_path, monkeypatch):
    cfg_file = tmp_path / "config.json"
    cfg_file.write_text(json.dumps({"base_url": "http://from-file:5000"}), encoding="utf-8")
    monkeypatch.setenv("DOCSTRANS_BASE_URL", "http://from-env:9000")
    cfg = load_config(config_path=cfg_file)
    assert cfg.base_url == "http://from-env:9000"
    assert cfg._sources["base_url"] == "env"


def test_config_cli_has_priority_over_env(tmp_path, monkeypatch):
    monkeypatch.setenv("DOCSTRANS_BASE_URL", "http://from-env:9000")
    cfg = load_config(config_path=tmp_path / "none.json", base_url="http://from-cli:1234")
    assert cfg.base_url == "http://from-cli:1234"
    assert cfg._sources["base_url"] == "cli"


def test_invalid_base_url_raises_config_error(tmp_path):
    with pytest.raises(ConfigError):
        load_config(config_path=tmp_path / "none.json", base_url="not-a-url")


def test_invalid_timeout_raises_config_error(tmp_path):
    with pytest.raises(ConfigError):
        load_config(config_path=tmp_path / "none.json", timeout=-1.0)


def test_invalid_json_config_raises(tmp_path):
    cfg_file = tmp_path / "bad.json"
    cfg_file.write_text("not json {{{{", encoding="utf-8")
    with pytest.raises(ConfigError):
        load_config(config_path=cfg_file)


def test_trailing_slash_stripped(tmp_path):
    cfg = load_config(config_path=tmp_path / "none.json", base_url="http://local:5000/")
    assert not cfg.base_url.endswith("/")
