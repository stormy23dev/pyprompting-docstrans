from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from docstrans.api.client import LibreTranslateClient
from docstrans.constants import PROVIDER, SUPPORTED_FILE_EXTENSIONS
from docstrans.db.glossary_repo import GlossaryRepo
from docstrans.db.history_repo import HistoryRepo
from docstrans.exceptions import FileOperationError
from docstrans.services.glossary_service import apply_glossary, restore_glossary
from docstrans.services.markdown_protection import (
    MarkdownSegment,
    protect_inline,
    restore_inline,
    split_markdown_segments,
)
from docstrans.services.segmentation import split_text

logger = logging.getLogger("docstrans.file")


@dataclass(frozen=True)
class FileTranslationResult:
    input_path: str
    output_path: str
    source_language: str
    target_language: str
    segments_translated: int
    provider: str
    saved_to_history: bool
    glossary_terms_applied: int


def default_output_path(input_path: Path, target: str) -> Path:
    return input_path.with_name(f"{input_path.stem}.{target}{input_path.suffix}")


def ensure_input_file(path: Path) -> None:
    if not path.exists():
        raise FileOperationError(f"Error: input file not found: {path}")
    if path.is_dir():
        raise FileOperationError(f"Error: input path is a directory: {path}")


def ensure_output_path(path: Path, *, overwrite: bool, create_dirs: bool) -> None:
    if path.exists() and not overwrite:
        raise FileOperationError(f"Error: output file already exists: {path}")
    if not path.parent.exists():
        if create_dirs:
            path.parent.mkdir(parents=True, exist_ok=True)
        else:
            raise FileOperationError(f"Error: output directory does not exist: {path.parent}")


class FileTranslationService:
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

    def translate_file(
        self,
        input_path: Path,
        *,
        output_path: Path | None,
        source: str,
        target: str,
        text_format: str,
        chunk_size: int,
        batch_size: int,
        preserve_markdown_code: bool,
        encoding: str,
        overwrite: bool,
        create_dirs: bool,
        save: bool,
    ) -> FileTranslationResult:
        ensure_input_file(input_path)
        output_path = output_path or default_output_path(input_path, target)
        ensure_output_path(output_path, overwrite=overwrite, create_dirs=create_dirs)
        try:
            source_text = input_path.read_text(encoding=encoding)
        except UnicodeDecodeError as exc:
            raise FileOperationError(f"Error: cannot decode file as {encoding}.") from exc
        except OSError as exc:
            raise FileOperationError(f"Error: cannot read input file: {input_path}") from exc

        if input_path.suffix.lower() not in SUPPORTED_FILE_EXTENSIONS:
            logger.warning(
                "Unsupported extension processed as plain text ext=%s", input_path.suffix
            )

        segments = self._make_segments(
            source_text, input_path.suffix.lower(), preserve_markdown_code
        )
        translated_text, segments_count, applied_count, total_duration, last_status = (
            self._translate_segments(
                segments,
                source=source,
                target=target,
                text_format=text_format,
                chunk_size=chunk_size,
                batch_size=batch_size,
            )
        )
        try:
            output_path.write_text(translated_text, encoding=encoding)
        except OSError as exc:
            raise FileOperationError(f"Error: cannot write output file: {output_path}") from exc

        if save:
            self.history_repo.add(
                kind="file",
                provider=PROVIDER,
                base_url=self.base_url,
                source_lang=source,
                target_lang=target,
                input_path=str(input_path),
                output_path=str(output_path),
                source_text=source_text,
                translated_text=translated_text,
                glossary_terms_applied=applied_count,
                api_status_code=last_status,
                duration_ms=total_duration,
            )
        return FileTranslationResult(
            input_path=str(input_path),
            output_path=str(output_path),
            source_language=source,
            target_language=target,
            segments_translated=segments_count,
            provider=PROVIDER,
            saved_to_history=save,
            glossary_terms_applied=applied_count,
        )

    def _make_segments(
        self, source_text: str, suffix: str, preserve_markdown_code: bool
    ) -> list[MarkdownSegment]:
        if suffix == ".md":
            return split_markdown_segments(source_text, preserve_code=preserve_markdown_code)
        return [MarkdownSegment(source_text, True)]

    def _translate_segments(
        self,
        segments: list[MarkdownSegment],
        *,
        source: str,
        target: str,
        text_format: str,
        chunk_size: int,
        batch_size: int,
    ) -> tuple[str, int, int, int, int | None]:
        terms = self.glossary_repo.list_for_translation(source_lang=source, target_lang=target)
        prepared: list[tuple[str, dict[str, str], dict[str, str]]] = []
        output_tokens: list[tuple[bool, int | str]] = []
        for segment in segments:
            if not segment.translatable:
                output_tokens.append((False, segment.text))
                continue
            for chunk in split_text(segment.text, chunk_size=chunk_size):
                if not chunk:
                    continue
                inline_protected, inline_map = protect_inline(chunk)
                glossary = apply_glossary(inline_protected, terms)
                prepared.append((glossary.text, inline_map, glossary.placeholders))
                output_tokens.append((True, len(prepared) - 1))

        translated_chunks: list[str] = [""] * len(prepared)
        total_duration = 0
        last_status: int | None = None
        for start in range(0, len(prepared), batch_size):
            batch = prepared[start : start + batch_size]
            q = [item[0] for item in batch]
            if not q:
                continue
            payload: str | list[str] = q[0] if len(q) == 1 else q
            translated, status_code, duration_ms = self.client.translate(
                payload, source=source, target=target, text_format=text_format
            )
            total_duration += duration_ms
            last_status = status_code
            if isinstance(translated, str):
                translated_list = [translated]
            else:
                translated_list = [str(item) for item in translated]
            if len(translated_list) != len(q):
                raise FileOperationError(
                    "Error: translation API returned unexpected segment count."
                )
            for offset, translated_text in enumerate(translated_list):
                _, inline_map, glossary_map = batch[offset]
                restored = restore_glossary(translated_text, glossary_map)
                restored = restore_inline(restored, inline_map)
                translated_chunks[start + offset] = restored

        rendered: list[str] = []
        for is_translated, value in output_tokens:
            if is_translated:
                rendered.append(translated_chunks[int(value)])
            else:
                rendered.append(str(value))
        applied_count = sum(len(glossary_map) for _, _, glossary_map in prepared)
        return "".join(rendered), len(prepared), applied_count, total_duration, last_status
