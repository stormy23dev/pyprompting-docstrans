from __future__ import annotations

import sqlite3


def test_translate_text_calls_translate_endpoint(runner, cli_base, fake_client):
    result = runner.invoke(
        app_import(), [*cli_base, "translate-text", "Hello", "--source", "en", "--target", "ru"]
    )
    assert result.exit_code == 0, result.output
    assert fake_client.requests[-1]["path"] == "/translate"
    assert fake_client.requests[-1]["q"] == "Hello"
    assert fake_client.requests[-1]["source"] == "en"
    assert fake_client.requests[-1]["target"] == "ru"
    assert fake_client.requests[-1]["format"] == "text"


def test_translate_text_saves_history(runner, cli_base, fake_client, tmp_path):
    result = runner.invoke(
        app_import(), [*cli_base, "translate-text", "Hello", "--source", "en", "--target", "ru"]
    )
    assert result.exit_code == 0, result.output
    conn = sqlite3.connect(tmp_path / "data.sqlite3")
    count = conn.execute("SELECT count(*) FROM translation_history").fetchone()[0]
    assert count == 1


def test_translate_text_no_save(runner, cli_base, fake_client, tmp_path):
    result = runner.invoke(app_import(), [*cli_base, "translate-text", "Hello", "--no-save"])
    assert result.exit_code == 0, result.output
    conn = sqlite3.connect(tmp_path / "data.sqlite3")
    count = conn.execute("SELECT count(*) FROM translation_history").fetchone()[0]
    assert count == 0


def app_import():
    from docstrans.cli import app

    return app
