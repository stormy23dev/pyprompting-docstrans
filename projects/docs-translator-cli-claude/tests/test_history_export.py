"""Tests for history listing and export."""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path

import httpx
import pytest
import respx
from typer.testing import CliRunner

from docstrans.cli import app
from docstrans.db.history_repo import add_text_entry, list_entries
from docstrans.services.export_service import export_history

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


def _seed_entries(conn, n: int = 3):
    for i in range(n):
        add_text_entry(
            conn,
            provider="libretranslate",
            base_url=BASE,
            source_lang="en",
            target_lang="ru",
            source_text=f"Hello {i}",
            translated_text=f"Привет {i}",
        )


# test_export_history_json_csv_md
def test_export_history_json_csv_md(tmp_path, tmp_db):
    _seed_entries(tmp_db, 3)
    entries = list_entries(tmp_db, limit=100)
    assert len(entries) == 3

    # JSON
    json_path = tmp_path / "history.json"
    export_history(entries, json_path, fmt="json", overwrite=False)
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert isinstance(data, list)
    assert len(data) == 3
    assert data[0]["kind"] == "text"

    # CSV
    csv_path = tmp_path / "history.csv"
    export_history(entries, csv_path, fmt="csv", overwrite=False)
    csv_content = csv_path.read_text(encoding="utf-8")
    reader = csv.DictReader(io.StringIO(csv_content))
    rows = list(reader)
    assert len(rows) == 3

    # MD
    md_path = tmp_path / "history.md"
    export_history(entries, md_path, fmt="md", overwrite=False)
    md_content = md_path.read_text(encoding="utf-8")
    assert "| ID |" in md_content
    md_lines = [ln for ln in md_content.splitlines() if ln.startswith("| ")]
    assert len(md_lines) == 5  # header + separator + 3 data rows


def test_export_refuses_overwrite_without_flag(tmp_path, tmp_db):
    _seed_entries(tmp_db)
    entries = list_entries(tmp_db)
    out = tmp_path / "out.json"
    out.write_text("existing", encoding="utf-8")
    from docstrans.exceptions import FileError

    with pytest.raises(FileError):
        export_history(entries, out, fmt="json", overwrite=False)


@respx.mock
def test_export_history_cli(tmp_path):
    env = _make_env(tmp_path)
    # First add a translation
    respx.post(f"{BASE}/translate").mock(
        return_value=httpx.Response(200, json={"translatedText": "Тест"})
    )
    runner.invoke(app, ["translate-text", "Test", "--source", "en", "--target", "ru"], env=env)

    out = tmp_path / "export.json"
    result = runner.invoke(app, ["export-history", str(out), "--format", "json"], env=env)
    assert result.exit_code == 0
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert len(data) >= 1
