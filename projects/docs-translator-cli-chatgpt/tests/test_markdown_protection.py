from __future__ import annotations

from docstrans.services.markdown_protection import (
    protect_inline,
    restore_inline,
    split_markdown_segments,
)


def test_markdown_code_blocks_are_not_translated(runner, cli_base, fake_client, tmp_path):
    md = tmp_path / "README.md"
    md.write_text(
        "# Title\n\n```python\nprint('hello')\n```\n\nUse `code` and https://example.com\n",
        encoding="utf-8",
    )
    result = runner.invoke(
        app_import(), [*cli_base, "translate-file", str(md), "--source", "en", "--target", "ru"]
    )
    assert result.exit_code == 0, result.output
    requests = fake_client.requests
    sent_payloads = []
    for request in requests:
        q = request.get("q")
        if isinstance(q, list):
            sent_payloads.extend(q)
        elif q:
            sent_payloads.append(q)
    sent = "\n".join(sent_payloads)
    assert "print('hello')" not in sent
    assert "`code`" not in sent
    assert "https://example.com" not in sent
    out = (tmp_path / "README.ru.md").read_text(encoding="utf-8")
    assert "print('hello')" in out
    assert "`code`" in out
    assert "https://example.com" in out


def test_inline_protect_restore():
    protected, mapping = protect_inline("Use `x` and https://example.com")
    assert "`x`" not in protected
    assert "https://example.com" not in protected
    assert restore_inline(protected, mapping) == "Use `x` and https://example.com"


def test_split_markdown_segments():
    segments = split_markdown_segments("A\n```\ncode\n```\nB\n")
    assert [s.translatable for s in segments] == [True, False, True]


def app_import():
    from docstrans.cli import app

    return app
