"""Tests for translate-text and detect-language CLI commands."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import respx
from typer.testing import CliRunner

from docstrans.cli import app
from docstrans.db.connection import get_connection
from docstrans.db.migrations import apply_migrations

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


# test_translate_text_calls_translate_endpoint (CLI level)
@respx.mock
def test_translate_text_calls_translate_endpoint(tmp_path):
    env = _make_env(tmp_path)
    respx.post(f"{BASE}/translate").mock(
        return_value=httpx.Response(200, json={"translatedText": "Привет мир"})
    )
    result = runner.invoke(
        app, ["translate-text", "Hello world", "--source", "en", "--target", "ru"], env=env
    )
    assert result.exit_code == 0, result.output
    assert "Привет мир" in result.output


# test_translate_text_saves_history
@respx.mock
def test_translate_text_saves_history(tmp_path):
    env = _make_env(tmp_path)
    respx.post(f"{BASE}/translate").mock(
        return_value=httpx.Response(200, json={"translatedText": "Готово"})
    )
    runner.invoke(app, ["translate-text", "Done", "--source", "en", "--target", "ru"], env=env)

    db_path = Path(env["DOCSTRANS_DB_PATH"])
    conn = get_connection(db_path)
    apply_migrations(conn)
    rows = conn.execute("SELECT * FROM translation_history").fetchall()
    assert len(rows) == 1
    assert rows[0]["kind"] == "text"
    assert rows[0]["source_text"] == "Done"


# test_translate_text_no_save
@respx.mock
def test_translate_text_no_save(tmp_path):
    env = _make_env(tmp_path)
    respx.post(f"{BASE}/translate").mock(
        return_value=httpx.Response(200, json={"translatedText": "OK"})
    )
    runner.invoke(
        app,
        ["translate-text", "OK", "--source", "en", "--target", "ru", "--no-save"],
        env=env,
    )

    db_path = Path(env["DOCSTRANS_DB_PATH"])
    conn = get_connection(db_path)
    apply_migrations(conn)
    rows = conn.execute("SELECT * FROM translation_history").fetchall()
    assert len(rows) == 0


# test_detect_language_calls_detect_endpoint
@respx.mock
def test_detect_language_calls_detect_endpoint(tmp_path):
    env = _make_env(tmp_path)
    respx.post(f"{BASE}/detect").mock(
        return_value=httpx.Response(200, json=[{"language": "fr", "confidence": 90.0}])
    )
    result = runner.invoke(app, ["detect-language", "Bonjour tout le monde"], env=env)
    assert result.exit_code == 0, result.output
    assert "fr" in result.output
    assert "90" in result.output


# test_api_429_maps_to_exit_code_12
@respx.mock
def test_api_429_maps_to_exit_code_12(tmp_path):
    env = _make_env(tmp_path)
    respx.post(f"{BASE}/translate").mock(
        return_value=httpx.Response(429, json={"error": "Slow down"})
    )
    result = runner.invoke(
        app, ["translate-text", "hello", "--source", "en", "--target", "ru"], env=env
    )
    assert result.exit_code == 12


# test_timeout_maps_to_exit_code_10
def test_timeout_maps_to_exit_code_10(tmp_path):
    env = _make_env(tmp_path)

    def _timeout_transport(request):
        raise httpx.TimeoutException("timed out")

    with patch("docstrans.cli._make_client") as mock_make:
        mock_client = MagicMock()
        mock_client.translate.side_effect = __import__(
            "docstrans.exceptions", fromlist=["NetworkError"]
        ).NetworkError("timeout")
        mock_make.return_value = mock_client
        result = runner.invoke(
            app,
            ["translate-text", "hello", "--source", "en", "--target", "ru"],
            env=env,
        )
    assert result.exit_code == 10
