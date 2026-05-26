from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner


class FakeClient:
    requests: list[dict[str, Any]] = []
    fail: Exception | None = None

    def __init__(self, *, base_url: str, api_key: str | None = None, timeout: float = 20.0) -> None:
        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout

    @classmethod
    def reset(cls) -> None:
        cls.requests = []
        cls.fail = None

    def translate(self, q, *, source: str, target: str, text_format: str = "text"):
        if FakeClient.fail:
            raise FakeClient.fail
        FakeClient.requests.append(
            {
                "method": "POST",
                "path": "/translate",
                "q": q,
                "source": source,
                "target": target,
                "format": text_format,
            }
        )
        if isinstance(q, list):
            return [f"TR:{item}" for item in q], 200, 12
        return f"TR:{q}", 200, 12

    def detect(self, q: str):
        FakeClient.requests.append({"method": "POST", "path": "/detect", "q": q})
        return [{"language": "fr", "confidence": 90.0}], 200, 5

    def languages(self):
        FakeClient.requests.append({"method": "GET", "path": "/languages"})
        return [{"code": "en", "name": "English", "targets": ["ru", "de"]}], 200, 5

    def health(self):
        FakeClient.requests.append({"method": "GET", "path": "/health"})
        return {"status": "ok"}, 200, 5


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch):
    for key in list(os.environ):
        if key.startswith("DOCSTRANS_"):
            monkeypatch.delenv(key, raising=False)


@pytest.fixture()
def fake_client(monkeypatch: pytest.MonkeyPatch):
    FakeClient.reset()
    monkeypatch.setattr("docstrans.cli.LibreTranslateClient", FakeClient)
    return FakeClient


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def cli_base(tmp_path: Path) -> list[str]:
    return [
        "--config-path",
        str(tmp_path / "config.json"),
        "--db-path",
        str(tmp_path / "data.sqlite3"),
        "--base-url",
        "http://test.local",
        "--no-color",
    ]
