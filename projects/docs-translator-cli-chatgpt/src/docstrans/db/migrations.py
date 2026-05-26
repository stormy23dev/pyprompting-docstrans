from __future__ import annotations

import sqlite3
from datetime import UTC, datetime

MIGRATION_VERSION = 1

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS glossary_terms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_lang TEXT NOT NULL,
    target_lang TEXT NOT NULL,
    source_term TEXT NOT NULL,
    source_term_norm TEXT NOT NULL,
    target_term TEXT NOT NULL,
    case_sensitive INTEGER NOT NULL DEFAULT 0,
    note TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(source_lang, target_lang, source_term_norm)
);

CREATE INDEX IF NOT EXISTS idx_glossary_langs
ON glossary_terms(source_lang, target_lang);

CREATE INDEX IF NOT EXISTS idx_glossary_search
ON glossary_terms(source_term_norm);

CREATE TABLE IF NOT EXISTS translation_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    kind TEXT NOT NULL CHECK(kind IN ('text', 'file')),
    provider TEXT NOT NULL,
    base_url TEXT NOT NULL,
    source_lang TEXT NOT NULL,
    target_lang TEXT NOT NULL,
    input_path TEXT,
    output_path TEXT,
    source_text TEXT,
    translated_text TEXT,
    source_hash TEXT NOT NULL,
    translated_hash TEXT NOT NULL,
    glossary_terms_applied INTEGER NOT NULL DEFAULT 0,
    api_status_code INTEGER,
    duration_ms INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_history_created_at
ON translation_history(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_history_langs
ON translation_history(source_lang, target_lang);

CREATE INDEX IF NOT EXISTS idx_history_hash
ON translation_history(source_hash, target_lang);
"""


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run_migrations(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_SQL)
    exists = conn.execute(
        "SELECT 1 FROM schema_migrations WHERE version = ?", (MIGRATION_VERSION,)
    ).fetchone()
    if not exists:
        conn.execute(
            "INSERT INTO schema_migrations(version, applied_at) VALUES (?, ?)",
            (MIGRATION_VERSION, utc_now()),
        )
    conn.commit()
