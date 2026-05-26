from __future__ import annotations

import hashlib
import sqlite3
from typing import Any

from docstrans.db.migrations import utc_now


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class HistoryRepo:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def add(
        self,
        *,
        kind: str,
        provider: str,
        base_url: str,
        source_lang: str,
        target_lang: str,
        source_text: str,
        translated_text: str,
        input_path: str | None = None,
        output_path: str | None = None,
        glossary_terms_applied: int = 0,
        api_status_code: int | None = None,
        duration_ms: int = 0,
    ) -> int:
        cur = self.conn.execute(
            """
            INSERT INTO translation_history(
                created_at, kind, provider, base_url, source_lang, target_lang, input_path,
                output_path, source_text, translated_text, source_hash, translated_hash,
                glossary_terms_applied, api_status_code, duration_ms
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                utc_now(),
                kind,
                provider,
                base_url,
                source_lang,
                target_lang,
                input_path,
                output_path,
                source_text[:10000],
                translated_text[:10000],
                sha256_text(source_text),
                sha256_text(translated_text),
                glossary_terms_applied,
                api_status_code,
                duration_ms,
            ),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def list(
        self,
        *,
        limit: int | None = 20,
        source_lang: str | None = None,
        target_lang: str | None = None,
        kind: str | None = None,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM translation_history WHERE 1=1"
        params: list[Any] = []
        if source_lang:
            query += " AND source_lang = ?"
            params.append(source_lang)
        if target_lang:
            query += " AND target_lang = ?"
            params.append(target_lang)
        if kind:
            query += " AND kind = ?"
            params.append(kind)
        query += " ORDER BY created_at DESC, id DESC"
        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)
        rows = self.conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]
