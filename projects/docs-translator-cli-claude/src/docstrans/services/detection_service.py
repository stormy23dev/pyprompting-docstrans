"""Language detection via REST API."""

from __future__ import annotations

from docstrans.api.client import TranslationClient
from docstrans.api.models import DetectResult


def detect_language(client: TranslationClient, text: str) -> list[DetectResult]:
    return client.detect(text)
