"""Repository for glossary_terms table."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _norm(term: str, case_sensitive: bool) -> str:
    return term if case_sensitive else term.lower()


@dataclass
class GlossaryTerm:
    id: int
    source_lang: str
    target_lang: str
    source_term: str
    target_term: str
    case_sensitive: bool
    note: str | None
    created_at: str
    updated_at: str


def _row_to_term(row: sqlite3.Row) -> GlossaryTerm:
    return GlossaryTerm(
        id=row["id"],
        source_lang=row["source_lang"],
        target_lang=row["target_lang"],
        source_term=row["source_term"],
        target_term=row["target_term"],
        case_sensitive=bool(row["case_sensitive"]),
        note=row["note"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def add_term(
    conn: sqlite3.Connection,
    source_lang: str,
    target_lang: str,
    source_term: str,
    target_term: str,
    case_sensitive: bool = False,
    note: str | None = None,
    replace: bool = False,
) -> GlossaryTerm:
    now = _now()
    norm = _norm(source_term, case_sensitive)

    existing = conn.execute(
        "SELECT id FROM glossary_terms WHERE source_lang=? AND target_lang=?"
        " AND source_term_norm=?",
        (source_lang, target_lang, _norm(source_term, False)),
    ).fetchone()

    if existing and not replace:
        from docstrans.exceptions import ConflictError

        raise ConflictError(
            f"Term already exists: {source_term!r} [{source_lang} -> {target_lang}]. Use --replace."
        )

    if existing and replace:
        conn.execute(
            """UPDATE glossary_terms
               SET source_term=?, source_term_norm=?, target_term=?, case_sensitive=?,
                   note=?, updated_at=?
               WHERE id=?""",
            (source_term, norm, target_term, int(case_sensitive), note, now, existing["id"]),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM glossary_terms WHERE id=?", (existing["id"],)).fetchone()
    else:
        conn.execute(
            """INSERT INTO glossary_terms
               (source_lang, target_lang, source_term, source_term_norm, target_term,
                case_sensitive, note, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                source_lang,
                target_lang,
                source_term,
                norm,
                target_term,
                int(case_sensitive),
                note,
                now,
                now,
            ),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM glossary_terms WHERE rowid=last_insert_rowid()"
        ).fetchone()

    return _row_to_term(row)


def list_terms(
    conn: sqlite3.Connection,
    source_lang: str | None = None,
    target_lang: str | None = None,
    search: str | None = None,
) -> list[GlossaryTerm]:
    sql = "SELECT * FROM glossary_terms WHERE 1=1"
    params: list = []
    if source_lang:
        sql += " AND source_lang=?"
        params.append(source_lang)
    if target_lang:
        sql += " AND target_lang=?"
        params.append(target_lang)
    if search:
        s = f"%{search.lower()}%"
        sql += " AND (source_term_norm LIKE ? OR LOWER(target_term) LIKE ?)"
        params.extend([s, s])
    sql += " ORDER BY id"
    rows = conn.execute(sql, params).fetchall()
    return [_row_to_term(r) for r in rows]


def remove_term(
    conn: sqlite3.Connection,
    source_term: str,
    source_lang: str,
    target_lang: str,
) -> bool:
    norm = _norm(source_term, False)
    cursor = conn.execute(
        "DELETE FROM glossary_terms WHERE source_lang=? AND target_lang=? AND source_term_norm=?",
        (source_lang, target_lang, norm),
    )
    conn.commit()
    return cursor.rowcount > 0


def get_terms_for_pair(
    conn: sqlite3.Connection, source_lang: str, target_lang: str
) -> list[GlossaryTerm]:
    rows = conn.execute(
        "SELECT * FROM glossary_terms WHERE source_lang=? AND target_lang=?"
        " ORDER BY LENGTH(source_term) DESC",
        (source_lang, target_lang),
    ).fetchall()
    return [_row_to_term(r) for r in rows]
