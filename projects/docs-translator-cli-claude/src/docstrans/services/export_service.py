"""Export translation history to various formats."""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path

from docstrans.db.history_repo import HistoryEntry
from docstrans.exceptions import FileError


def _preview(text: str | None, length: int = 50) -> str:
    if not text:
        return ""
    t = text.replace("\n", " ")
    return t[:length] + "..." if len(t) > length else t


def export_json(entries: list[HistoryEntry], path: Path, overwrite: bool = False) -> None:
    _check_overwrite(path, overwrite)
    data = [
        {
            "id": e.id,
            "created_at": e.created_at,
            "kind": e.kind,
            "provider": e.provider,
            "base_url": e.base_url,
            "source_lang": e.source_lang,
            "target_lang": e.target_lang,
            "input_path": e.input_path,
            "output_path": e.output_path,
            "source_text": e.source_text,
            "translated_text": e.translated_text,
            "source_hash": e.source_hash,
            "translated_hash": e.translated_hash,
            "glossary_terms_applied": e.glossary_terms_applied,
            "duration_ms": e.duration_ms,
        }
        for e in entries
    ]
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def export_csv(entries: list[HistoryEntry], path: Path, overwrite: bool = False) -> None:
    _check_overwrite(path, overwrite)
    buf = io.StringIO()
    fieldnames = [
        "id",
        "created_at",
        "kind",
        "source_lang",
        "target_lang",
        "source_preview",
        "result_preview",
        "input_path",
        "output_path",
        "duration_ms",
    ]
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    for e in entries:
        writer.writerow(
            {
                "id": e.id,
                "created_at": e.created_at,
                "kind": e.kind,
                "source_lang": e.source_lang,
                "target_lang": e.target_lang,
                "source_preview": _preview(e.source_text),
                "result_preview": _preview(e.translated_text),
                "input_path": e.input_path or "",
                "output_path": e.output_path or "",
                "duration_ms": e.duration_ms,
            }
        )
    path.write_text(buf.getvalue(), encoding="utf-8")


def export_md(entries: list[HistoryEntry], path: Path, overwrite: bool = False) -> None:
    _check_overwrite(path, overwrite)
    lines = [
        "| ID | Created at | Kind | Langs | Source preview | Result preview |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for e in entries:
        langs = f"{e.source_lang}->{e.target_lang}"
        lines.append(
            f"| {e.id} | {e.created_at} | {e.kind} | {langs} "
            f"| {_preview(e.source_text, 40)} | {_preview(e.translated_text, 40)} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _check_overwrite(path: Path, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise FileError(f"Output file exists, use --overwrite: {path}")


def export_history(
    entries: list[HistoryEntry],
    output_path: Path,
    fmt: str,
    overwrite: bool = False,
    create_dirs: bool = False,
) -> None:
    if create_dirs:
        output_path.parent.mkdir(parents=True, exist_ok=True)
    if fmt == "json":
        export_json(entries, output_path, overwrite)
    elif fmt == "csv":
        export_csv(entries, output_path, overwrite)
    elif fmt == "md":
        export_md(entries, output_path, overwrite)
    else:
        raise ValueError(f"Unknown export format: {fmt}")
