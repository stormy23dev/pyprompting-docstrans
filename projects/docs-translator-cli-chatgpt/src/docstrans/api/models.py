from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Detection:
    language: str
    confidence: float


@dataclass(frozen=True)
class Language:
    code: str
    name: str
    targets: list[str]
