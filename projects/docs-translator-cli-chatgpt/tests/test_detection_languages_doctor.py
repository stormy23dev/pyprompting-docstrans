from __future__ import annotations


def test_detect_language_calls_detect_endpoint(runner, cli_base, fake_client):
    result = runner.invoke(app_import(), [*cli_base, "detect-language", "Bonjour"])
    assert result.exit_code == 0, result.output
    assert "Language: fr" in result.output
    assert fake_client.requests[-1]["path"] == "/detect"


def test_languages_list_calls_languages_endpoint(runner, cli_base, fake_client):
    result = runner.invoke(app_import(), [*cli_base, "languages-list"])
    assert result.exit_code == 0, result.output
    assert "English" in result.output
    assert fake_client.requests[-1]["path"] == "/languages"


def test_doctor_skip_api(runner, cli_base, fake_client):
    result = runner.invoke(app_import(), [*cli_base, "doctor", "--skip-api"])
    assert result.exit_code == 0, result.output
    assert "REST API: skipped" in result.output


def app_import():
    from docstrans.cli import app

    return app
