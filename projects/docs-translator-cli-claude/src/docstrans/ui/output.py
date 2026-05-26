"""Rich-based output helpers for CLI commands."""

from __future__ import annotations

import json
import sys
from typing import Any

from rich.console import Console
from rich.table import Table

_stdout = Console(highlight=False)
_stderr = Console(stderr=True, highlight=False)


def print_ok(msg: str) -> None:
    _stdout.print(msg)


def print_err(msg: str) -> None:
    _stderr.print(f"[bold red]Error:[/bold red] {msg}")


def print_json(data: Any) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def print_table(
    title: str | None,
    columns: list[str],
    rows: list[list[str]],
    no_color: bool = False,
) -> None:
    console = Console(highlight=False, no_color=no_color)
    table = Table(show_header=True, header_style="bold" if not no_color else "")
    for col in columns:
        table.add_column(col)
    for row in rows:
        table.add_row(*row)
    if title:
        console.print(f"\n[bold]{title}[/bold]")
    console.print(table)


def err_exit(msg: str, code: int = 1) -> None:
    print_err(msg)
    sys.exit(code)
