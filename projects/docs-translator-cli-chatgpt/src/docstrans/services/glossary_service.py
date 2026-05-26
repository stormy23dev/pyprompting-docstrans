from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

WORD_CHARS = "A-Za-zА-Яа-яЁё0-9_"
logger = logging.getLogger("docstrans.glossary")


@dataclass
class GlossaryApplication:
    text: str
    placeholders: dict[str, str] = field(default_factory=dict)
    applied_count: int = 0


def _term_pattern(term: str, *, case_sensitive: bool) -> re.Pattern[str]:
    escaped = re.escape(term)
    flags = 0 if case_sensitive else re.IGNORECASE
    return re.compile(rf"(?<![{WORD_CHARS}]){escaped}(?![{WORD_CHARS}])", flags)


def apply_glossary(text: str, terms: list[dict]) -> GlossaryApplication:
    result = text
    placeholders: dict[str, str] = {}
    counter = 1
    applied_count = 0
    ordered = sorted(terms, key=lambda item: len(item["source_term"]), reverse=True)
    for term in ordered:
        source_term = term["source_term"]
        target_term = term["target_term"]
        case_sensitive = bool(term.get("case_sensitive", 0))
        pattern = _term_pattern(source_term, case_sensitive=case_sensitive)

        def replace(_: re.Match[str], replacement: str = target_term) -> str:
            nonlocal counter, applied_count
            token = f"DTGLOSSARYTOKEN{counter:06d}"
            placeholders[token] = replacement
            counter += 1
            applied_count += 1
            return token

        result = pattern.sub(replace, result)
    return GlossaryApplication(result, placeholders, applied_count)


def restore_glossary(text: str, placeholders: dict[str, str]) -> str:
    result = text
    for token, target_term in placeholders.items():
        if token not in result:
            logger.warning("Glossary placeholder missing in API response token=%s", token)
        result = result.replace(token, target_term)
    return result
