"""Tests for file translation service."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest
import respx
from typer.testing import CliRunner

from docstrans.cli import app
from docstrans.exceptions import FileError
from docstrans.services.file_service import translate_file

runner = CliRunner()
BASE = "http://localhost:5000"


def _make_env(tmp_path: Path) -> dict:
    db = tmp_path / "db.sqlite3"
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps({"base_url": BASE}), encoding="utf-8")
    return {
        "DOCSTRANS_CONFIG_PATH": str(cfg),
        "DOCSTRANS_DB_PATH": str(db),
    }


# test_translate_file_creates_default_output
@respx.mock
def test_translate_file_creates_default_output(tmp_path):
    env = _make_env(tmp_path)
    readme = tmp_path / "README.md"
    readme.write_text("Hello world\n\nSecond paragraph\n", encoding="utf-8")

    respx.post(f"{BASE}/translate").mock(
        return_value=httpx.Response(200, json={"translatedText": ["Привет мир", "Второй абзац"]})
    )

    result = runner.invoke(
        app,
        ["translate-file", str(readme), "--source", "en", "--target", "ru"],
        env=env,
    )
    assert result.exit_code == 0, result.output
    expected_output = tmp_path / "README.ru.md"
    assert expected_output.exists()
    content = expected_output.read_text(encoding="utf-8")
    assert len(content) > 0


# test_translate_file_refuses_overwrite_without_flag
@respx.mock
def test_translate_file_refuses_overwrite_without_flag(tmp_path):
    env = _make_env(tmp_path)
    readme = tmp_path / "README.md"
    readme.write_text("Hello\n", encoding="utf-8")
    existing_output = tmp_path / "README.ru.md"
    existing_output.write_text("Already exists\n", encoding="utf-8")

    result = runner.invoke(
        app,
        ["translate-file", str(readme), "--source", "en", "--target", "ru"],
        env=env,
    )
    assert result.exit_code == 5  # EXIT_FILE
    # Original file untouched
    assert existing_output.read_text() == "Already exists\n"


def test_translate_file_nonexistent_input(tmp_path, tmp_db):
    from docstrans.api.client import TranslationClient

    fake_path = tmp_path / "nonexistent.md"
    client = TranslationClient.__new__(TranslationClient)
    with pytest.raises(FileError, match="not found"):
        translate_file(client, tmp_db, fake_path, source="en", target="ru")
