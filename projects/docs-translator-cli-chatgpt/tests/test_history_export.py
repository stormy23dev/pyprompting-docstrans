from __future__ import annotations


def test_export_history_json_csv_md(runner, cli_base, fake_client, tmp_path):
    app = app_import()
    assert (
        runner.invoke(
            app, [*cli_base, "translate-text", "Hello", "--source", "en", "--target", "ru"]
        ).exit_code
        == 0
    )
    for ext, fmt in [("json", "json"), ("csv", "csv"), ("md", "md")]:
        out = tmp_path / f"history.{ext}"
        result = runner.invoke(
            app, [*cli_base, "export-history", str(out), "--format", fmt, "--overwrite"]
        )
        assert result.exit_code == 0, result.output
        assert out.exists()
        assert out.read_text(encoding="utf-8")


def test_history_list_empty(runner, cli_base):
    result = runner.invoke(app_import(), [*cli_base, "history-list"])
    assert result.exit_code == 0, result.output
    assert "No translation history found" in result.output


def app_import():
    from docstrans.cli import app

    return app
