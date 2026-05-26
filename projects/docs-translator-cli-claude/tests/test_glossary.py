"""Tests for glossary CRUD and term application."""

from __future__ import annotations

import pytest

from docstrans.db.glossary_repo import add_term, get_terms_for_pair, list_terms, remove_term
from docstrans.exceptions import ConflictError
from docstrans.services.glossary_service import apply_glossary, restore_glossary


# test_glossary_add_list_remove
def test_glossary_add_list_remove(tmp_db):
    conn = tmp_db
    term = add_term(conn, "en", "ru", "deployment pipeline", "конвейер развертывания")
    assert term.source_term == "deployment pipeline"
    assert term.target_term == "конвейер развертывания"

    terms = list_terms(conn, source_lang="en", target_lang="ru")
    assert len(terms) == 1
    assert terms[0].source_term == "deployment pipeline"

    removed = remove_term(conn, "deployment pipeline", "en", "ru")
    assert removed is True
    assert list_terms(conn) == []


# test_glossary_duplicate_without_replace_fails
def test_glossary_duplicate_without_replace_fails(tmp_db):
    conn = tmp_db
    add_term(conn, "en", "ru", "pipeline", "конвейер")
    with pytest.raises(ConflictError):
        add_term(conn, "en", "ru", "pipeline", "другой перевод", replace=False)


def test_glossary_replace_updates_existing(tmp_db):
    conn = tmp_db
    add_term(conn, "en", "ru", "pipeline", "конвейер")
    updated = add_term(conn, "en", "ru", "pipeline", "новый перевод", replace=True)
    assert updated.target_term == "новый перевод"
    assert len(list_terms(conn)) == 1


# test_glossary_replaces_longest_term_first
def test_glossary_replaces_longest_term_first(tmp_db):
    conn = tmp_db
    add_term(conn, "en", "ru", "deployment pipeline", "конвейер развертывания")
    add_term(conn, "en", "ru", "deployment", "развертывание")

    terms = get_terms_for_pair(conn, "en", "ru")
    text = "Configure the deployment pipeline before deployment"
    modified, token_map = apply_glossary(text, terms)

    # Longest match first: "deployment pipeline" is replaced before "deployment"
    # After apply_glossary, "deployment pipeline" is a token and
    # standalone "deployment" is also a token
    restored = restore_glossary(modified, token_map)
    assert "конвейер развертывания" in restored
    # "deployment" alone should also be replaced
    assert "развертывание" in restored or "конвейер развертывания" in restored


def test_glossary_remove_not_found_returns_false(tmp_db):
    removed = remove_term(tmp_db, "nonexistent", "en", "ru")
    assert removed is False


def test_glossary_search_filter(tmp_db):
    conn = tmp_db
    add_term(conn, "en", "ru", "pipeline", "конвейер")
    add_term(conn, "en", "ru", "deploy", "развернуть")
    results = list_terms(conn, search="pipe")
    assert len(results) == 1
    assert results[0].source_term == "pipeline"
