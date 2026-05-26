"""Protect Markdown code blocks and inline code from translation."""

from __future__ import annotations

import re

_FENCED_RE = re.compile(r"(```+|~~~+).*?\n.*?\1", re.DOTALL)
_INLINE_CODE_RE = re.compile(r"`[^`\n]+`")
_URL_RE = re.compile(r"https?://\S+")

_TOKEN_FMT = "\x00MDPROTECT{index:06d}\x00"


def protect_markdown(text: str) -> tuple[str, dict[str, str]]:
    """Replace protected regions with tokens. Returns (modified_text, token_map)."""
    token_map: dict[str, str] = {}
    index = 0

    def replace(m: re.Match) -> str:
        nonlocal index
        tok = _TOKEN_FMT.format(index=index)
        token_map[tok] = m.group(0)
        index += 1
        return tok

    text = _FENCED_RE.sub(replace, text)
    text = _INLINE_CODE_RE.sub(replace, text)
    text = _URL_RE.sub(replace, text)
    return text, token_map


def restore_markdown(text: str, token_map: dict[str, str]) -> str:
    """Restore protected regions from tokens."""
    for tok, original in token_map.items():
        text = text.replace(tok, original)
    return text
