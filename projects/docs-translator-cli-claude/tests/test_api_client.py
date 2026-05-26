"""Tests for the API client (mocked with respx)."""

from __future__ import annotations

import httpx
import pytest
import respx

from docstrans.api.client import TranslationClient
from docstrans.exceptions import AuthError, NetworkError, RateLimitError, ServerError

BASE = "http://test-api.local"


def make_client(**kwargs) -> TranslationClient:
    http = httpx.Client()
    return TranslationClient(base_url=BASE, client=http, **kwargs)


# test_translate_text_calls_translate_endpoint
@respx.mock
def test_translate_text_calls_translate_endpoint():
    """POST /translate is called with correct q, source, target, format."""
    route = respx.post(f"{BASE}/translate").mock(
        return_value=httpx.Response(200, json={"translatedText": "Привет, мир"})
    )
    client = make_client()
    resp = client.translate("Hello world", source="en", target="ru", fmt="text")

    assert route.called
    body = route.calls[0].request
    import json

    sent = json.loads(body.content)
    assert sent["q"] == "Hello world"
    assert sent["source"] == "en"
    assert sent["target"] == "ru"
    assert sent["format"] == "text"
    assert resp.translated_text == "Привет, мир"


@respx.mock
def test_translate_batch_returns_list():
    respx.post(f"{BASE}/translate").mock(
        return_value=httpx.Response(200, json={"translatedText": ["Один", "Два"]})
    )
    client = make_client()
    resp = client.translate(["One", "Two"], source="en", target="ru")
    assert isinstance(resp.translated_text, list)
    assert resp.translated_text == ["Один", "Два"]


@respx.mock
def test_detect_calls_detect_endpoint():
    respx.post(f"{BASE}/detect").mock(
        return_value=httpx.Response(200, json=[{"language": "fr", "confidence": 90.0}])
    )
    client = make_client()
    results = client.detect("Bonjour")
    assert results[0].language == "fr"
    assert results[0].confidence == 90.0


@respx.mock
def test_languages_list_calls_languages_endpoint():
    respx.get(f"{BASE}/languages").mock(
        return_value=httpx.Response(
            200, json=[{"code": "en", "name": "English", "targets": ["ru"]}]
        )
    )
    client = make_client()
    langs = client.languages()
    assert langs[0].code == "en"
    assert langs[0].name == "English"


@respx.mock
def test_api_401_maps_to_auth_error():
    respx.post(f"{BASE}/translate").mock(
        return_value=httpx.Response(401, json={"error": "Unauthorized"})
    )
    client = make_client()
    with pytest.raises(AuthError):
        client.translate("test", source="en", target="ru")


@respx.mock
def test_api_429_maps_to_rate_limit_error():
    respx.post(f"{BASE}/translate").mock(
        return_value=httpx.Response(429, json={"error": "Slow down"})
    )
    client = make_client()
    with pytest.raises(RateLimitError):
        client.translate("test", source="en", target="ru")


@respx.mock
def test_api_500_maps_to_server_error():
    respx.post(f"{BASE}/translate").mock(
        return_value=httpx.Response(500, json={"error": "Internal Server Error"})
    )
    client = make_client()
    with pytest.raises(ServerError):
        client.translate("test", source="en", target="ru")


def test_timeout_maps_to_network_error():
    """Timeout raises NetworkError (no respx needed – we raise manually)."""

    def _raise(_r):
        raise httpx.TimeoutException("timeout")

    http = httpx.Client(transport=httpx.MockTransport(_raise))
    client = TranslationClient(base_url=BASE, client=http)
    with pytest.raises(NetworkError):
        client.translate("test", source="en", target="ru")


@respx.mock
def test_api_key_added_when_configured():
    route = respx.post(f"{BASE}/translate").mock(
        return_value=httpx.Response(200, json={"translatedText": "ok"})
    )
    client = TranslationClient(base_url=BASE, api_key="secret123", client=httpx.Client())
    client.translate("hi", source="en", target="ru")
    import json

    body = json.loads(route.calls[0].request.content)
    assert body.get("api_key") == "secret123"
