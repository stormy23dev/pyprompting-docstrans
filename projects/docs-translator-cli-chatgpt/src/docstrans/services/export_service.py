from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from docstrans.constants import SUPPORTED_EXPORT_FORMATS
from docstrans.db.history_repo import HistoryRepo
from docstrans.exceptions import FileOperationError

EXPORT_FIELDS = [
    "id",
    "created_at",
    "kind",
    "provider",
    "base_url",
    "source_lang",
    "target_lang",
    "input_path",
    "output_path",
    "source_text",
    "translated_text",
    "source_hash",
    "translated_hash",
    "glossary_terms_applied",
    "api_status_code",
    "duration_ms",
]


def infer_format(path: Path, requested: str | None) -> str:
    if requested:
        return requested
    suffix = path.suffix.lower().lstrip(".")
    return suffix if suffix in SUPPORTED_EXPORT_FORMATS else "json"


class ExportService:
    def __init__(self, history_repo: HistoryRepo) -> None:
        self.history_repo = history_repo

    def export(
        self,
        output_path: Path,
        *,
        export_format: str | None,
        limit: int | None,
        source_lang: str | None,
        target_lang: str | None,
        overwrite: bool,
        create_dirs: bool,
    ) -> int:
        fmt = infer_format(output_path, export_format)
        if fmt not in SUPPORTED_EXPORT_FORMATS:
            raise FileOperationError(f"Error: unsupported export format: {fmt}")
        if output_path.exists() and not overwrite:
            raise FileOperationError(f"Error: output file already exists: {output_path}")
        if not output_path.parent.exists():
            if create_dirs:
                output_path.parent.mkdir(parents=True, exist_ok=True)
            else:
                raise FileOperationError(
                    f"Error: output directory does not exist: {output_path.parent}"
                )
        records = self.history_repo.list(
            limit=limit, source_lang=source_lang, target_lang=target_lang, kind=None
        )
        if fmt == "json":
            self._write_json(output_path, records)
        elif fmt == "csv":
            self._write_csv(output_path, records)
        else:
            self._write_md(output_path, records)
        return len(records)

    def _write_json(self, output_path: Path, records: list[dict[str, Any]]) -> None:
        output_path.write_text(
            json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    def _write_csv(self, output_path: Path, records: list[dict[str, Any]]) -> None:
        with output_path.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=EXPORT_FIELDS, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(records)

    def _write_md(self, output_path: Path, records: list[dict[str, Any]]) -> None:
        lines = [
            "| ID | Created at | Kind | Langs | Source preview | Result preview |",
            "|---:|---|---|---|---|---|",
        ]
        for row in records:
            source = _md_cell(_preview(row.get("source_text") or ""))
            target = _md_cell(_preview(row.get("translated_text") or ""))
            lines.append(
                f"| {row['id']} | {row['created_at']} | {row['kind']} | "
                f"{row['source_lang']}->{row['target_lang']} | {source} | {target} |"
            )
        output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _preview(value: str, limit: int = 60) -> str:
    one_line = " ".join(value.split())
    return one_line if len(one_line) <= limit else one_line[: limit - 3] + "..."


def _md_cell(value: str) -> str:
    return value.replace("|", "\\|")
