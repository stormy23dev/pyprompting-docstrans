"""Apply and restore glossary terms around API translation."""

from __future__ import annotations

import re

from docstrans.constants import GLOSSARY_TOKEN_PREFIX
from docstrans.db.glossary_repo import GlossaryTerm


def _make_token(index: int) -> str:
    return f"{GLOSSARY_TOKEN_PREFIX}{index:06d}"


def apply_glossary(text: str, terms: list[GlossaryTerm]) -> tuple[str, dict[str, str]]:
    """Replace glossary source terms with tokens. Returns (modified_text, token->target_term)."""
    token_map: dict[str, str] = {}
    used: list[tuple[str, str]] = []  # (token, target_term)

    # Sort by length descending so longer terms are replaced first
    sorted_terms = sorted(terms, key=lambda t: len(t.source_term), reverse=True)

    index = 0
    for term in sorted_terms:
        flags = 0 if term.case_sensitive else re.IGNORECASE
        pattern = r"(?<!\w)" + re.escape(term.source_term) + r"(?!\w)"
        try:
            compiled = re.compile(pattern, flags)
        except re.error:
            continue

        if compiled.search(text):
            token = _make_token(index)
            token_map[token] = term.target_term
            used.append((token, term.target_term))
            text = compiled.sub(token, text)
            index += 1

    return text, token_map


def restore_glossary(text: str, token_map: dict[str, str]) -> str:
    """Replace placeholder tokens with target terms."""
    for token, target in token_map.items():
        text = text.replace(token, target) if token in text else text
    return text
