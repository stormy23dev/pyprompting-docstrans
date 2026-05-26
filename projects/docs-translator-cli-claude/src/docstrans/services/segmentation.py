"""Split large text into segments for batch API translation."""

from __future__ import annotations

import logging
import re

log = logging.getLogger("docstrans.segmentation")


def _split_by_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [p for p in parts if p]


def _split_by_words(text: str, chunk_size: int) -> list[str]:
    words = text.split()
    segments: list[str] = []
    current: list[str] = []
    current_len = 0
    for word in words:
        if current_len + len(word) + 1 > chunk_size and current:
            segments.append(" ".join(current))
            current = []
            current_len = 0
        current.append(word)
        current_len += len(word) + 1
    if current:
        segments.append(" ".join(current))
    return segments


def segment_text(text: str, chunk_size: int = 4000) -> list[str]:
    """Split text into segments no larger than chunk_size characters."""
    if not text.strip():
        return []

    # Split by blank lines first
    paragraphs = re.split(r"\n{2,}", text)
    segments: list[str] = []

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if len(para) <= chunk_size:
            segments.append(para)
            continue
        # Try splitting by sentences
        sentences = _split_by_sentences(para)
        current_parts: list[str] = []
        current_len = 0
        for sentence in sentences:
            if len(sentence) > chunk_size:
                if current_parts:
                    segments.append(" ".join(current_parts))
                    current_parts = []
                    current_len = 0
                # Split by words
                word_segs = _split_by_words(sentence, chunk_size)
                for ws in word_segs:
                    if len(ws) > chunk_size:
                        log.warning(
                            "Single word longer than chunk_size=%d: %d chars",
                            chunk_size,
                            len(ws),
                        )
                    segments.append(ws)
            elif current_len + len(sentence) + 1 > chunk_size:
                if current_parts:
                    segments.append(" ".join(current_parts))
                current_parts = [sentence]
                current_len = len(sentence)
            else:
                current_parts.append(sentence)
                current_len += len(sentence) + 1
        if current_parts:
            segments.append(" ".join(current_parts))

    return [s for s in segments if s.strip()]
