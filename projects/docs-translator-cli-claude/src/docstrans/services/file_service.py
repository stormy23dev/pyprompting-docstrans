"""File translation service: segment, translate, reassemble."""

from __future__ import annotations

import logging
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path

from docstrans.api.client import TranslationClient
from docstrans.db import glossary_repo, history_repo
from docstrans.exceptions import FileError
from docstrans.services.glossary_service import apply_glossary, restore_glossary
from docstrans.services.markdown_protection import protect_markdown, restore_markdown
from docstrans.services.segmentation import segment_text

log = logging.getLogger("docstrans.file")

_MAX_HISTORY_TEXT = 10_000


@dataclass
class FileTranslationResult:
    input_path: str
    output_path: str
    source_lang: str
    target_lang: str
    segments_translated: int
    glossary_terms_applied: int
    saved_to_history: bool
    duration_ms: int


def _default_output(input_path: Path, target: str) -> Path:
    stem = input_path.stem
    suffix = input_path.suffix
    return input_path.parent / f"{stem}.{target}{suffix}"


def translate_file(
    client: TranslationClient,
    conn: sqlite3.Connection,
    input_path: Path,
    source: str,
    target: str,
    output_path: Path | None = None,
    overwrite: bool = False,
    create_dirs: bool = False,
    encoding: str = "utf-8",
    fmt: str = "text",
    chunk_size: int = 4000,
    batch_size: int = 20,
    preserve_markdown_code: bool = True,
    save: bool = True,
    provider: str = "libretranslate",
) -> FileTranslationResult:
    if not input_path.exists():
        raise FileError(f"Input file not found: {input_path}")
    if input_path.is_dir():
        raise FileError(f"Input path is a directory: {input_path}")

    try:
        source_text = input_path.read_text(encoding=encoding)
    except UnicodeDecodeError as e:
        raise FileError(f"Cannot decode file as {encoding}: {input_path}") from e

    resolved_output = output_path or _default_output(input_path, target)

    if resolved_output.exists() and not overwrite:
        raise FileError(f"Output file exists, use --overwrite: {resolved_output}")

    if create_dirs:
        resolved_output.parent.mkdir(parents=True, exist_ok=True)

    suffix = input_path.suffix.lower()
    use_md_protection = preserve_markdown_code and suffix == ".md"

    working_text = source_text
    md_token_map: dict[str, str] = {}
    if use_md_protection:
        working_text, md_token_map = protect_markdown(source_text)

    terms = glossary_repo.get_terms_for_pair(conn, source if source != "auto" else "en", target)
    working_text, gloss_token_map = apply_glossary(working_text, terms)
    terms_applied = len(gloss_token_map)

    segments = segment_text(working_text, chunk_size=chunk_size)
    log.debug("translate_file segments=%d input=%s", len(segments), input_path)

    # Mark segments that consist only of protection tokens (should not be translated)
    import re as _re

    _token_only_re = _re.compile(r"^(\x00MDPROTECT\d+\x00\s*)+$")

    def _is_protected(seg: str) -> bool:
        return bool(_token_only_re.match(seg.strip()))

    # Build ordered list of (segment, is_protected)
    tagged: list[tuple[str, bool]] = [(s, _is_protected(s)) for s in segments]

    # Only translate non-protected segments, preserving order
    translate_indices = [i for i, (_, prot) in enumerate(tagged) if not prot]
    translate_segs = [tagged[i][0] for i in translate_indices]

    translated_map: dict[int, str] = {}
    start = time.monotonic()

    i = 0
    while i < len(translate_segs):
        batch = translate_segs[i : i + batch_size]
        batch_orig_indices = translate_indices[i : i + batch_size]
        if len(batch) == 1:
            resp = client.translate(batch[0], source=source, target=target, fmt=fmt)
            result = resp.translated_text
            translated_map[batch_orig_indices[0]] = (
                result[0] if isinstance(result, list) else result
            )
        else:
            resp = client.translate(batch, source=source, target=target, fmt=fmt)
            result = resp.translated_text
            results_list = result if isinstance(result, list) else [result]
            for j, orig_idx in enumerate(batch_orig_indices):
                translated_map[orig_idx] = results_list[j] if j < len(results_list) else batch[j]
        i += batch_size

    duration_ms = int((time.monotonic() - start) * 1000)

    # Reassemble in order
    final_segments: list[str] = []
    for idx, (seg, is_prot) in enumerate(tagged):
        if is_prot:
            final_segments.append(seg)
        else:
            final_segments.append(translated_map.get(idx, seg))

    translated_text = "\n\n".join(final_segments)
    translated_text = restore_glossary(translated_text, gloss_token_map)
    if use_md_protection:
        translated_text = restore_markdown(translated_text, md_token_map)

    # Preserve trailing newline
    if source_text.endswith("\n") and not translated_text.endswith("\n"):
        translated_text += "\n"

    try:
        resolved_output.write_text(translated_text, encoding=encoding)
    except OSError as e:
        raise FileError(f"Cannot write output file: {e}") from e

    if save:
        history_repo.add_file_entry(
            conn,
            provider=provider,
            base_url=client.base_url,
            source_lang=source,
            target_lang=target,
            input_path=str(input_path),
            output_path=str(resolved_output),
            source_text=source_text,
            translated_text=translated_text,
            glossary_terms_applied=terms_applied,
            duration_ms=duration_ms,
        )

    return FileTranslationResult(
        input_path=str(input_path),
        output_path=str(resolved_output),
        source_lang=source,
        target_lang=target,
        segments_translated=len(segments),
        glossary_terms_applied=terms_applied,
        saved_to_history=save,
        duration_ms=duration_ms,
    )
