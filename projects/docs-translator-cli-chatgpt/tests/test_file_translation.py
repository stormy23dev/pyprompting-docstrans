from __future__ import annotations


def test_translate_file_creates_default_output(runner, cli_base, fake_client, tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text("Hello world\n", encoding="utf-8")
    result = runner.invoke(
        app_import(), [*cli_base, "translate-file", str(readme), "--source", "en", "--target", "ru"]
    )
    assert result.exit_code == 0, result.output
    output = tmp_path / "README.ru.md"
    assert output.exists()
    assert "TR:Hello world" in output.read_text(encoding="utf-8")


def test_translate_file_refuses_overwrite_without_flag(runner, cli_base, fake_client, tmp_path):
    readme = tmp_path / "README.md"
    output = tmp_path / "README.ru.md"
    readme.write_text("Hello world\n", encoding="utf-8")
    output.write_text("existing", encoding="utf-8")
    result = runner.invoke(
        app_import(), [*cli_base, "translate-file", str(readme), "--target", "ru"]
    )
    assert result.exit_code == 5


def app_import():
    from docstrans.cli import app

    return app
