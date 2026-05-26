from __future__ import annotations

import sqlite3
from typing import Any

from docstrans.db.migrations import utc_now
from docstrans.exceptions import LocalConflictError, LocalNotFoundError


def normalize_term(value: str, *, case_sensitive: bool = False) -> str:
    value = " ".join(value.strip().split())
    return value if case_sensitive else value.casefold()


class GlossaryRepo:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def add(
        self,
        *,
        source_term: str,
        target_term: str,
        source_lang: str,
        target_lang: str,
        case_sensitive: bool = False,
        note: str | None = None,
        replace: bool = False,
    ) -> int:
        source_term = source_term.strip()
        target_term = target_term.strip()
        if not source_term or not target_term:
            raise ValueError("terms cannot be empty")
        now = utc_now()
        norm = normalize_term(source_term, case_sensitive=case_sensitive)
        try:
            cur = self.conn.execute(
                """
                INSERT INTO glossary_terms(
                    source_lang, target_lang, source_term, source_term_norm, target_term,
                    case_sensitive, note, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
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
        except sqlite3.IntegrityError as exc:
            if not replace:
                raise LocalConflictError("Error: glossary term already exists.") from exc
            self.conn.execute(
                """
                UPDATE glossary_terms
                SET source_term = ?, target_term = ?, case_sensitive = ?, note = ?, updated_at = ?
                WHERE source_lang = ? AND target_lang = ? AND source_term_norm = ?
                """,
                (
                    source_term,
                    target_term,
                    int(case_sensitive),
                    note,
                    now,
                    source_lang,
                    target_lang,
                    norm,
                ),
            )
            row = self.conn.execute(
                """
                SELECT id FROM glossary_terms
                WHERE source_lang = ? AND target_lang = ? AND source_term_norm = ?
                """,
                (source_lang, target_lang, norm),
            ).fetchone()
            self.conn.commit()
            return int(row["id"])
        self.conn.commit()
        return int(cur.lastrowid)

    def list(
        self,
        *,
        source_lang: str | None = None,
        target_lang: str | None = None,
        search: str | None = None,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM glossary_terms WHERE 1=1"
        params: list[Any] = []
        if source_lang:
            query += " AND source_lang = ?"
            params.append(source_lang)
        if target_lang:
            query += " AND target_lang = ?"
            params.append(target_lang)
        if search:
            query += " AND (source_term_norm LIKE ? OR target_term LIKE ?)"
            params.extend([f"%{search.casefold()}%", f"%{search}%"])
        query += " ORDER BY source_lang, target_lang, length(source_term) DESC, source_term"
        rows = self.conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def list_for_translation(self, *, source_lang: str, target_lang: str) -> list[dict[str, Any]]:
        if source_lang == "auto":
            rows = self.conn.execute(
                """
                SELECT * FROM glossary_terms
                WHERE target_lang = ?
                ORDER BY length(source_term) DESC, source_term
                """,
                (target_lang,),
            ).fetchall()
        else:
            rows = self.conn.execute(
                """
                SELECT * FROM glossary_terms
                WHERE source_lang = ? AND target_lang = ?
                ORDER BY length(source_term) DESC, source_term
                """,
                (source_lang, target_lang),
            ).fetchall()
        return [dict(row) for row in rows]

    def remove(self, *, source_term: str, source_lang: str, target_lang: str) -> None:
        norm = normalize_term(source_term)
        cur = self.conn.execute(
            """
            DELETE FROM glossary_terms
            WHERE source_lang = ? AND target_lang = ? AND source_term_norm = ?
            """,
            (source_lang, target_lang, norm),
        )
        self.conn.commit()
        if cur.rowcount == 0:
            raise LocalNotFoundError("Glossary term not found.")
