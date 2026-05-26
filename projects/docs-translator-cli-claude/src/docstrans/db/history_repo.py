"""Repository for translation_history table."""

from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass
class HistoryEntry:
    id: int
    created_at: str
    kind: str
    provider: str
    base_url: str
    source_lang: str
    target_lang: str
    input_path: str | None
    output_path: str | None
    source_text: str | None
    translated_text: str | None
    source_hash: str
    translated_hash: str
    glossary_terms_applied: int
    api_status_code: int | None
    duration_ms: int


def _row_to_entry(row: sqlite3.Row) -> HistoryEntry:
    return HistoryEntry(
        id=row["id"],
        created_at=row["created_at"],
        kind=row["kind"],
        provider=row["provider"],
        base_url=row["base_url"],
        source_lang=row["source_lang"],
        target_lang=row["target_lang"],
        input_path=row["input_path"],
        output_path=row["output_path"],
        source_text=row["source_text"],
        translated_text=row["translated_text"],
        source_hash=row["source_hash"],
        translated_hash=row["translated_hash"],
        glossary_terms_applied=row["glossary_terms_applied"],
        api_status_code=row["api_status_code"],
        duration_ms=row["duration_ms"],
    )


def add_text_entry(
    conn: sqlite3.Connection,
    *,
    provider: str,
    base_url: str,
    source_lang: str,
    target_lang: str,
    source_text: str,
    translated_text: str,
    glossary_terms_applied: int = 0,
    duration_ms: int = 0,
) -> HistoryEntry:
    row_id = conn.execute(
        """INSERT INTO translation_history
           (created_at, kind, provider, base_url, source_lang, target_lang,
            source_text, translated_text, source_hash, translated_hash,
            glossary_terms_applied, duration_ms)
           VALUES (?, 'text', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            _now(),
            provider,
            base_url,
            source_lang,
            target_lang,
            source_text,
            translated_text,
            sha256(source_text),
            sha256(translated_text),
            glossary_terms_applied,
            duration_ms,
        ),
    ).lastrowid
    conn.commit()
    row = conn.execute("SELECT * FROM translation_history WHERE id=?", (row_id,)).fetchone()
    return _row_to_entry(row)


def add_file_entry(
    conn: sqlite3.Connection,
    *,
    provider: str,
    base_url: str,
    source_lang: str,
    target_lang: str,
    input_path: str,
    output_path: str,
    source_text: str,
    translated_text: str,
    glossary_terms_applied: int = 0,
    duration_ms: int = 0,
) -> HistoryEntry:
    row_id = conn.execute(
        """INSERT INTO translation_history
           (created_at, kind, provider, base_url, source_lang, target_lang,
            input_path, output_path, source_text, translated_text,
            source_hash, translated_hash, glossary_terms_applied, duration_ms)
           VALUES (?, 'file', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            _now(),
            provider,
            base_url,
            source_lang,
            target_lang,
            input_path,
            output_path,
            source_text[:10000],
            translated_text[:10000],
            sha256(source_text),
            sha256(translated_text),
            glossary_terms_applied,
            duration_ms,
        ),
    ).lastrowid
    conn.commit()
    row = conn.execute("SELECT * FROM translation_history WHERE id=?", (row_id,)).fetchone()
    return _row_to_entry(row)


def list_entries(
    conn: sqlite3.Connection,
    limit: int = 20,
    source_lang: str | None = None,
    target_lang: str | None = None,
    kind: str | None = None,
) -> list[HistoryEntry]:
    sql = "SELECT * FROM translation_history WHERE 1=1"
    params: list = []
    if source_lang:
        sql += " AND source_lang=?"
        params.append(source_lang)
    if target_lang:
        sql += " AND target_lang=?"
        params.append(target_lang)
    if kind:
        sql += " AND kind=?"
        params.append(kind)
    sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(sql, params).fetchall()
    return [_row_to_entry(r) for r in rows]
