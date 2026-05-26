from __future__ import annotations

import httpx
import pytest

from docstrans.api.client import LibreTranslateClient
from docstrans.exceptions import ApiRateLimitError, NetworkError


def test_api_429_maps_to_exit_code_12(monkeypatch):
    class Client:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def request(self, *args, **kwargs):
            return httpx.Response(
                429,
                json={"error": "Slow down"},
                request=httpx.Request("POST", "http://x/translate"),
            )

    monkeypatch.setattr("docstrans.api.client.httpx.Client", Client)
    client = LibreTranslateClient(base_url="http://x")
    with pytest.raises(ApiRateLimitError) as exc:
        client.translate("Hello", source="en", target="ru")
    assert exc.value.exit_code == 12
    assert "Slow down" in str(exc.value)


def test_timeout_maps_to_exit_code_10(monkeypatch):
    class Client:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def request(self, *args, **kwargs):
            raise httpx.TimeoutException("timeout")

    monkeypatch.setattr("docstrans.api.client.httpx.Client", Client)
    client = LibreTranslateClient(base_url="http://x", timeout=1)
    with pytest.raises(NetworkError) as exc:
        client.translate("Hello", source="en", target="ru")
    assert exc.value.exit_code == 10
