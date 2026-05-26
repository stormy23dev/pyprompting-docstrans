"""Dataclass models for LibreTranslate API responses."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TranslateResponse:
    translated_text: str | list[str]


@dataclass
class DetectResult:
    language: str
    confidence: float


@dataclass
class LanguageInfo:
    code: str
    name: str
    targets: list[str] = field(default_factory=list)
