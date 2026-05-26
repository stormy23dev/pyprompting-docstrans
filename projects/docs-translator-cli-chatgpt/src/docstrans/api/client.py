from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from docstrans.exceptions import (
    ApiAuthError,
    ApiBadRequestError,
    ApiRateLimitError,
    ApiServerError,
    NetworkError,
)

logger = logging.getLogger("docstrans.api")


class LibreTranslateClient:
    def __init__(self, *, base_url: str, api_key: str | None = None, timeout: float = 20.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def _json_with_key(self, payload: dict[str, Any]) -> dict[str, Any]:
        if self.api_key:
            return {**payload, "api_key": self.api_key}
        return payload

    def _api_error_text(self, response: httpx.Response) -> str | None:
        try:
            data = response.json()
        except ValueError:
            return None
        if isinstance(data, dict) and isinstance(data.get("error"), str):
            return data["error"]
        return None

    def _handle_status(self, response: httpx.Response) -> None:
        if 200 <= response.status_code < 300:
            return
        api_text = self._api_error_text(response)
        suffix = f": {api_text}" if api_text else ""
        if response.status_code == 400:
            raise ApiBadRequestError(f"Error: invalid translation API request{suffix}.")
        if response.status_code in {401, 403}:
            raise ApiAuthError(f"Error: API key is missing or invalid{suffix}.")
        if response.status_code == 429:
            raise ApiRateLimitError(f"Error: API rate limit exceeded{suffix}.")
        if 500 <= response.status_code <= 599:
            raise ApiServerError(f"Error: translation API server error{suffix}.")
        raise ApiBadRequestError(
            f"Error: translation API returned HTTP {response.status_code}{suffix}."
        )

    def _request(self, method: str, path: str, **kwargs: Any) -> tuple[Any, int, int]:
        url = f"{self.base_url}{path}"
        start = time.perf_counter()
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.request(method, url, **kwargs)
            duration_ms = int((time.perf_counter() - start) * 1000)
            self._handle_status(response)
            logger.info(
                "API request completed method=%s path=%s status=%s duration_ms=%s",
                method,
                path,
                response.status_code,
                duration_ms,
            )
            return response.json(), response.status_code, duration_ms
        except httpx.TimeoutException as exc:
            raise NetworkError(
                f"Error: translation API timeout after {self.timeout} seconds."
            ) from exc
        except (httpx.ConnectError, httpx.NetworkError) as exc:
            raise NetworkError("Error: cannot connect to translation API.") from exc
        except httpx.HTTPError as exc:
            raise NetworkError("Error: translation API HTTP error.") from exc

    def translate(
        self,
        q: str | list[str],
        *,
        source: str,
        target: str,
        text_format: str = "text",
    ) -> tuple[str | list[str], int, int]:
        payload = self._json_with_key(
            {"q": q, "source": source, "target": target, "format": text_format}
        )
        data, status_code, duration_ms = self._request(
            "POST", "/translate", json=payload, headers={"Content-Type": "application/json"}
        )
        if not isinstance(data, dict) or "translatedText" not in data:
            raise ApiServerError("Error: translation API returned invalid response.")
        return data["translatedText"], status_code, duration_ms

    def detect(self, q: str) -> tuple[list[dict[str, Any]], int, int]:
        payload = self._json_with_key({"q": q})
        data, status_code, duration_ms = self._request(
            "POST", "/detect", json=payload, headers={"Content-Type": "application/json"}
        )
        if not isinstance(data, list):
            raise ApiServerError("Error: detect API returned invalid response.")
        return data, status_code, duration_ms

    def languages(self) -> tuple[list[dict[str, Any]], int, int]:
        data, status_code, duration_ms = self._request("GET", "/languages")
        if not isinstance(data, list):
            raise ApiServerError("Error: languages API returned invalid response.")
        return data, status_code, duration_ms

    def health(self) -> tuple[dict[str, Any], int, int]:
        data, status_code, duration_ms = self._request("GET", "/health")
        if not isinstance(data, dict):
            raise ApiServerError("Error: health API returned invalid response.")
        return data, status_code, duration_ms
