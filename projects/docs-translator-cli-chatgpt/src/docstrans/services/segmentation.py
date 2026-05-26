from __future__ import annotations

import logging
import re

logger = logging.getLogger("docstrans.segmentation")
_SENTENCE_RE = re.compile(r"(?<=[.!?。！？])\s+")


def split_text(text: str, *, chunk_size: int) -> list[str]:
    if not text:
        return []
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    result: list[str] = []
    parts = re.split(r"(\n\s*\n)", text)
    for part in parts:
        if not part:
            continue
        if len(part) <= chunk_size:
            result.append(part)
            continue
        result.extend(_split_long_part(part, chunk_size=chunk_size))
    return result


def _split_long_part(text: str, *, chunk_size: int) -> list[str]:
    sentences = _SENTENCE_RE.split(text)
    result: list[str] = []
    current = ""
    for sentence in sentences:
        if len(sentence) > chunk_size:
            if current:
                result.append(current)
                current = ""
            result.extend(_split_words(sentence, chunk_size=chunk_size))
        elif len(current) + len(sentence) + (1 if current else 0) <= chunk_size:
            current = f"{current} {sentence}" if current else sentence
        else:
            if current:
                result.append(current)
            current = sentence
    if current:
        result.append(current)
    return result


def _split_words(text: str, *, chunk_size: int) -> list[str]:
    words = text.split(" ")
    result: list[str] = []
    current = ""
    for word in words:
        if len(word) > chunk_size:
            logger.warning(
                "Word longer than chunk_size length=%s chunk_size=%s", len(word), chunk_size
            )
            if current:
                result.append(current)
                current = ""
            result.append(word)
        elif len(current) + len(word) + (1 if current else 0) <= chunk_size:
            current = f"{current} {word}" if current else word
        else:
            if current:
                result.append(current)
            current = word
    if current:
        result.append(current)
    return result
