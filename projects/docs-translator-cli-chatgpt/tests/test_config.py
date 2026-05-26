from __future__ import annotations

import json

from docstrans.config import build_config


def test_config_env_has_priority_over_file(tmp_path, monkeypatch):
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"base_url": "http://file", "timeout": 10}), encoding="utf-8")
    monkeypatch.setenv("DOCSTRANS_BASE_URL", "http://env")
    config = build_config(config_path=config_path)
    assert config.base_url == "http://env"
    assert config.sources["base_url"] == "env"


def test_config_set_and_show_masks_api_key(runner, cli_base):
    result = runner.invoke(app_import(), [*cli_base, "config-set", "api_key", "secret"])
    assert result.exit_code == 0, result.output
    assert "************" in result.output
    assert "secret" not in result.output
    show = runner.invoke(app_import(), [*cli_base, "config-show"])
    assert show.exit_code == 0, show.output
    assert "secret" not in show.output


def app_import():
    from docstrans.cli import app

    return app
