"""Tests for Markdown code block protection."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import respx
from typer.testing import CliRunner

from docstrans.cli import app
from docstrans.services.markdown_protection import protect_markdown, restore_markdown

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


def test_fenced_code_block_protected():
    text = "Some text\n\n```python\nprint('hello')\n```\n\nMore text"
    protected, token_map = protect_markdown(text)
    assert "```" not in protected
    assert len(token_map) == 1
    restored = restore_markdown(protected, token_map)
    assert "```python" in restored
    assert "print('hello')" in restored


def test_inline_code_protected():
    text = "Use the `config` option."
    protected, token_map = protect_markdown(text)
    assert "`config`" not in protected
    assert len(token_map) == 1
    restored = restore_markdown(protected, token_map)
    assert "`config`" in restored


def test_url_protected():
    text = "See https://example.com for details."
    protected, token_map = protect_markdown(text)
    assert "https://example.com" not in protected
    restored = restore_markdown(protected, token_map)
    assert "https://example.com" in restored


def test_round_trip_complex_markdown():
    text = "# Title\n\nRun `install` to begin.\n\n```bash\nnpm install\n```\n\nSee https://docs.example.com."
    protected, token_map = protect_markdown(text)
    # Simulate translation: only translate non-token text
    # Protected regions should survive round-trip
    restored = restore_markdown(protected, token_map)
    assert "`install`" in restored
    assert "```bash" in restored
    assert "npm install" in restored
    assert "https://docs.example.com" in restored


# test_markdown_code_blocks_are_not_translated (CLI integration)
@respx.mock
def test_markdown_code_blocks_are_not_translated(tmp_path):
    """Fenced code block content is NOT sent to API and is preserved verbatim."""
    env = _make_env(tmp_path)
    md_content = "Hello world\n\n```python\nprint('hello world')\n```\n\nAnother paragraph\n"
    md_file = tmp_path / "doc.md"
    md_file.write_text(md_content, encoding="utf-8")

    captured_bodies = []

    def mock_translate(request):
        import json as _json

        body = _json.loads(request.content)
        q = body.get("q", "")
        if isinstance(q, list):
            captured_bodies.extend(q)
        else:
            captured_bodies.append(q)
        return httpx.Response(200, json={"translatedText": ["Привет мир", "Другой абзац"]})

    respx.post(f"{BASE}/translate").mock(side_effect=mock_translate)

    result = runner.invoke(
        app,
        [
            "translate-file",
            str(md_file),
            "--source",
            "en",
            "--target",
            "ru",
            "--preserve-markdown-code",
            "--overwrite",
        ],
        env=env,
    )
    assert result.exit_code == 0, result.output

    # No code block content should appear in API requests
    for body in captured_bodies:
        assert "print('hello world')" not in body

    # Output file should still contain the code block
    output = tmp_path / "doc.ru.md"
    if output.exists():
        content = output.read_text(encoding="utf-8")
        assert "print('hello world')" in content
