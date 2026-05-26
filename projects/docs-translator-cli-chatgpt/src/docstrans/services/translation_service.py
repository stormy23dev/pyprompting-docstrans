from __future__ import annotations

from dataclasses import dataclass

from docstrans.api.client import LibreTranslateClient
from docstrans.constants import PROVIDER
from docstrans.db.glossary_repo import GlossaryRepo
from docstrans.db.history_repo import HistoryRepo
from docstrans.services.glossary_service import apply_glossary, restore_glossary


@dataclass(frozen=True)
class TranslationResult:
    translated_text: str
    source_language: str
    target_language: str
    provider: str
    saved_to_history: bool
    glossary_terms_applied: int
    api_status_code: int
    duration_ms: int


class TranslationService:
    def __init__(
        self,
        *,
        client: LibreTranslateClient,
        glossary_repo: GlossaryRepo,
        history_repo: HistoryRepo,
        base_url: str,
    ) -> None:
        self.client = client
        self.glossary_repo = glossary_repo
        self.history_repo = history_repo
        self.base_url = base_url

    def translate_text(
        self,
        text: str,
        *,
        source: str,
        target: str,
        text_format: str = "text",
        save: bool = True,
    ) -> TranslationResult:
        terms = self.glossary_repo.list_for_translation(source_lang=source, target_lang=target)
        glossary = apply_glossary(text, terms)
        translated, status_code, duration_ms = self.client.translate(
            glossary.text, source=source, target=target, text_format=text_format
        )
        if not isinstance(translated, str):
            translated = "\n".join(str(item) for item in translated)
        restored = restore_glossary(translated, glossary.placeholders)
        if save:
            self.history_repo.add(
                kind="text",
                provider=PROVIDER,
                base_url=self.base_url,
                source_lang=source,
                target_lang=target,
                source_text=text,
                translated_text=restored,
                glossary_terms_applied=glossary.applied_count,
                api_status_code=status_code,
                duration_ms=duration_ms,
            )
        return TranslationResult(
            translated_text=restored,
            source_language=source,
            target_language=target,
            provider=PROVIDER,
            saved_to_history=save,
            glossary_terms_applied=glossary.applied_count,
            api_status_code=status_code,
            duration_ms=duration_ms,
        )
