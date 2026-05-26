"""History service helpers."""

from __future__ import annotations

import sqlite3

from docstrans.db import history_repo
from docstrans.db.history_repo import HistoryEntry


def get_history(
    conn: sqlite3.Connection,
    limit: int = 20,
    source_lang: str | None = None,
    target_lang: str | None = None,
    kind: str | None = None,
) -> list[HistoryEntry]:
    return history_repo.list_entries(
        conn, limit=limit, source_lang=source_lang, target_lang=target_lang, kind=kind
    )
