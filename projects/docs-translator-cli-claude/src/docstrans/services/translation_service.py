"""High-level translation service combining API client, glossary, and history."""

from __future__ import annotations

import logging
import sqlite3
import time
from dataclasses import dataclass

from docstrans.api.client import TranslationClient
from docstrans.db import glossary_repo, history_repo
from docstrans.services.glossary_service import apply_glossary, restore_glossary

log = logging.getLogger("docstrans.translation")


@dataclass
class TextTranslationResult:
    source_lang: str
    target_lang: str
    translated_text: str
    glossary_terms_applied: int
    saved_to_history: bool
    duration_ms: int


def translate_text(
    client: TranslationClient,
    conn: sqlite3.Connection,
    text: str,
    source: str,
    target: str,
    fmt: str = "text",
    save: bool = True,
    provider: str = "libretranslate",
) -> TextTranslationResult:
    terms = glossary_repo.get_terms_for_pair(conn, source if source != "auto" else "en", target)

    modified_text, token_map = apply_glossary(text, terms)
    terms_applied = len(token_map)

    start = time.monotonic()
    resp = client.translate(modified_text, source=source, target=target, fmt=fmt)
    duration_ms = int((time.monotonic() - start) * 1000)

    result_text = resp.translated_text
    if isinstance(result_text, list):
        result_text = result_text[0] if result_text else ""

    result_text = restore_glossary(result_text, token_map)

    log.debug(
        "Text translation done source=%s target=%s duration_ms=%d glossary_applied=%d",
        source,
        target,
        duration_ms,
        terms_applied,
    )

    if save:
        history_repo.add_text_entry(
            conn,
            provider=provider,
            base_url=client.base_url,
            source_lang=source,
            target_lang=target,
            source_text=text,
            translated_text=result_text,
            glossary_terms_applied=terms_applied,
            duration_ms=duration_ms,
        )

    return TextTranslationResult(
        source_lang=source,
        target_lang=target,
        translated_text=result_text,
        glossary_terms_applied=terms_applied,
        saved_to_history=save,
        duration_ms=duration_ms,
    )
