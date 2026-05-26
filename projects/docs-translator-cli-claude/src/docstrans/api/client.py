"""HTTP client for the LibreTranslate-compatible REST API."""

from __future__ import annotations

import contextlib
import logging

import httpx

from docstrans.api.models import DetectResult, LanguageInfo, TranslateResponse
from docstrans.exceptions import (
    AuthError,
    BadRequestError,
    NetworkError,
    RateLimitError,
    ServerError,
)

log = logging.getLogger("docstrans.api")


def _safe_url(url: str) -> str:
    """Strip api_key from logged URLs (api_key is never in URL for LibreTranslate, but be safe)."""
    return url


def _handle_status(response: httpx.Response) -> None:
    status = response.status_code
    if status == 200:
        return
    body: dict = {}
    with contextlib.suppress(Exception):
        body = response.json()
    api_msg = body.get("error", "")

    if status in (401, 403):
        msg = "API key is missing or invalid"
        if api_msg:
            msg += f": {api_msg}"
        raise AuthError(msg)
    if status == 429:
        msg = "API rate limit exceeded"
        if api_msg:
            msg += f": {api_msg}"
        raise RateLimitError(msg)
    if status == 400:
        msg = "invalid translation API request"
        if api_msg:
            msg += f": {api_msg}"
        raise BadRequestError(msg)
    if 500 <= status < 600:
        msg = "translation API server error"
        if api_msg:
            msg += f": {api_msg}"
        raise ServerError(msg)
    response.raise_for_status()


class TranslationClient:
    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        timeout: float = 20.0,
        client: httpx.Client | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self._client = client or httpx.Client(timeout=timeout)
        self._owns_client = client is None

    def _build_body(self, extra: dict) -> dict:
        body = dict(extra)
        if self.api_key:
            body["api_key"] = self.api_key
        return body

    def translate(
        self,
        q: str | list[str],
        source: str,
        target: str,
        fmt: str = "text",
    ) -> TranslateResponse:
        url = f"{self.base_url}/translate"
        body = self._build_body({"q": q, "source": source, "target": target, "format": fmt})
        log.debug("translate request source=%s target=%s url=%s", source, target, _safe_url(url))
        try:
            resp = self._client.post(url, json=body)
        except httpx.TimeoutException as e:
            raise NetworkError(f"translation API timeout after {self.timeout} seconds") from e
        except (httpx.ConnectError, httpx.NetworkError, httpx.HTTPError) as e:
            raise NetworkError(f"translation API connection error: {e}") from e

        _handle_status(resp)
        data = resp.json()
        log.debug("translate response status=%d", resp.status_code)
        return TranslateResponse(translated_text=data["translatedText"])

    def detect(self, q: str) -> list[DetectResult]:
        url = f"{self.base_url}/detect"
        body = self._build_body({"q": q})
        log.debug("detect request url=%s", _safe_url(url))
        try:
            resp = self._client.post(url, json=body)
        except httpx.TimeoutException as e:
            raise NetworkError(f"translation API timeout after {self.timeout} seconds") from e
        except (httpx.ConnectError, httpx.NetworkError, httpx.HTTPError) as e:
            raise NetworkError(f"translation API connection error: {e}") from e

        _handle_status(resp)
        data = resp.json()
        log.debug("detect response status=%d results=%d", resp.status_code, len(data))
        return [DetectResult(language=d["language"], confidence=d["confidence"]) for d in data]

    def languages(self) -> list[LanguageInfo]:
        url = f"{self.base_url}/languages"
        log.debug("languages request url=%s", _safe_url(url))
        try:
            resp = self._client.get(url)
        except httpx.TimeoutException as e:
            raise NetworkError(f"translation API timeout after {self.timeout} seconds") from e
        except (httpx.ConnectError, httpx.NetworkError, httpx.HTTPError) as e:
            raise NetworkError(f"translation API connection error: {e}") from e

        _handle_status(resp)
        data = resp.json()
        log.debug("languages response status=%d count=%d", resp.status_code, len(data))
        return [
            LanguageInfo(code=d["code"], name=d["name"], targets=d.get("targets", [])) for d in data
        ]

    def health(self) -> dict:
        url = f"{self.base_url}/health"
        log.debug("health request url=%s", _safe_url(url))
        try:
            resp = self._client.get(url)
        except httpx.TimeoutException as e:
            raise NetworkError(f"translation API timeout after {self.timeout} seconds") from e
        except (httpx.ConnectError, httpx.NetworkError, httpx.HTTPError) as e:
            raise NetworkError(f"translation API connection error: {e}") from e

        _handle_status(resp)
        return resp.json()

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> TranslationClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
