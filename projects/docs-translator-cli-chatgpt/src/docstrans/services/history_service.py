from __future__ import annotations

from docstrans.db.history_repo import HistoryRepo


class HistoryService:
    def __init__(self, repo: HistoryRepo) -> None:
        self.repo = repo

    def list(
        self, *, limit: int, source_lang: str | None, target_lang: str | None, kind: str | None
    ):
        return self.repo.list(
            limit=limit, source_lang=source_lang, target_lang=target_lang, kind=kind
        )
