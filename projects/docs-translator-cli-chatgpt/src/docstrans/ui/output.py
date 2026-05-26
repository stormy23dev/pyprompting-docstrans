from __future__ import annotations

import json
from typing import Any

from rich.console import Console
from rich.table import Table


def make_console(*, no_color: bool = False, stderr: bool = False) -> Console:
    return Console(no_color=no_color, stderr=stderr)


def print_json(console: Console, payload: Any) -> None:
    console.print(json.dumps(payload, ensure_ascii=False, indent=2))


def make_table(title: str | None, columns: list[str]) -> Table:
    table = Table(title=title)
    for column in columns:
        table.add_column(column)
    return table


def preview(value: str | None, limit: int = 28) -> str:
    if not value:
        return ""
    one_line = " ".join(value.split())
    return one_line if len(one_line) <= limit else one_line[: limit - 3] + "..."
