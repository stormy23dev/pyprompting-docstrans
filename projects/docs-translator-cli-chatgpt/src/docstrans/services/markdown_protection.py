from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class MarkdownSegment:
    text: str
    translatable: bool


INLINE_PATTERN = re.compile(r"(`[^`\n]+`|https?://\S+)")


def split_markdown_segments(text: str, *, preserve_code: bool = True) -> list[MarkdownSegment]:
    if not preserve_code:
        return [MarkdownSegment(text, True)]
    lines = text.splitlines(keepends=True)
    segments: list[MarkdownSegment] = []
    buffer: list[str] = []
    code_buffer: list[str] = []
    in_fence = False
    fence_marker: str | None = None

    def flush_text() -> None:
        if buffer:
            segments.append(MarkdownSegment("".join(buffer), True))
            buffer.clear()

    def flush_code() -> None:
        if code_buffer:
            segments.append(MarkdownSegment("".join(code_buffer), False))
            code_buffer.clear()

    for line in lines:
        stripped = line.lstrip()
        is_fence = stripped.startswith("```") or stripped.startswith("~~~")
        marker = stripped[:3] if is_fence else None
        if is_fence and not in_fence:
            flush_text()
            in_fence = True
            fence_marker = marker
            code_buffer.append(line)
        elif is_fence and in_fence and marker == fence_marker:
            code_buffer.append(line)
            in_fence = False
            fence_marker = None
            flush_code()
        elif in_fence:
            code_buffer.append(line)
        else:
            buffer.append(line)
    if in_fence:
        flush_code()
    flush_text()
    return segments


def protect_inline(text: str) -> tuple[str, dict[str, str]]:
    mapping: dict[str, str] = {}
    counter = 1

    def replace(match: re.Match[str]) -> str:
        nonlocal counter
        token = f"DTPROTECTEDTOKEN{counter:06d}"
        mapping[token] = match.group(0)
        counter += 1
        return token

    return INLINE_PATTERN.sub(replace, text), mapping


def restore_inline(text: str, mapping: dict[str, str]) -> str:
    result = text
    for token, original in mapping.items():
        result = result.replace(token, original)
    return result
