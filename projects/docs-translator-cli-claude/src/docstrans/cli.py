"""Docstrans CLI – main Typer application."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from docstrans import __version__
from docstrans.api.client import TranslationClient
from docstrans.config import AppConfig, load_config, write_config_key
from docstrans.constants import (
    DEFAULT_BATCH_SIZE,
    DEFAULT_CHUNK_SIZE,
    EXIT_CONFIG,
    EXIT_INTERNAL,
    EXIT_NETWORK,
    EXIT_NOT_FOUND,
    SUPPORTED_EXTENSIONS,
)
from docstrans.db.connection import get_connection
from docstrans.db.migrations import apply_migrations
from docstrans.exceptions import (
    ConflictError,
    DocstransError,
    FileError,
)
from docstrans.logging_setup import setup_logging

app = typer.Typer(
    name="docstrans",
    help="Translate documentation files via a LibreTranslate-compatible REST API.",
    no_args_is_help=True,
    add_completion=False,
)

_stderr = Console(stderr=True, highlight=False)
_stdout = Console(highlight=False)


# ── global option state ──────────────────────────────────────────────────────


class _State:
    config: AppConfig | None = None
    verbose: bool = False
    no_color: bool = False


_state = _State()


def _get_config() -> AppConfig:
    if _state.config is None:
        _state.config = load_config()
    return _state.config


def _init_db(cfg: AppConfig):
    conn = get_connection(cfg.db_path)
    apply_migrations(conn)
    return conn


def _make_client(
    cfg: AppConfig,
    base_url: str | None = None,
    api_key: str | None = None,
) -> TranslationClient:
    url = base_url or cfg.base_url
    key = api_key or cfg.api_key
    return TranslationClient(base_url=url, api_key=key, timeout=cfg.timeout)


def _handle_error(e: Exception, verbose: bool = False) -> None:
    import logging

    log = logging.getLogger("docstrans.cli")
    if isinstance(e, DocstransError):
        _stderr.print(f"[bold red]Error:[/bold red] {e.message}")
        log.error("Command error: %s", e.message)
        raise typer.Exit(code=e.exit_code)
    _stderr.print(f"[bold red]Error:[/bold red] {e}")
    if verbose:
        import traceback

        _stderr.print(traceback.format_exc())
    log.exception("Unexpected error")
    raise typer.Exit(code=EXIT_INTERNAL)


# ── enums for CLI options ────────────────────────────────────────────────────


class FormatEnum(StrEnum):
    text = "text"
    html = "html"


class ExportFormatEnum(StrEnum):
    json = "json"
    csv = "csv"
    md = "md"


class KindEnum(StrEnum):
    text = "text"
    file = "file"


class ConfigKeyEnum(StrEnum):
    base_url = "base_url"
    api_key = "api_key"
    default_source = "default_source"
    default_target = "default_target"
    timeout = "timeout"


# ── callback (global options) ────────────────────────────────────────────────


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    config_path: Annotated[
        Path | None, typer.Option("--config-path", help="Path to config file.")
    ] = None,
    db_path: Annotated[Path | None, typer.Option("--db-path", help="Path to SQLite DB.")] = None,
    base_url: Annotated[
        str | None, typer.Option("--base-url", help="LibreTranslate API URL.")
    ] = None,
    api_key: Annotated[
        str | None, typer.Option("--api-key", help="API key (masked in output).")
    ] = None,
    timeout: Annotated[
        float | None, typer.Option("--timeout", help="HTTP timeout in seconds.")
    ] = None,
    verbose: Annotated[bool, typer.Option("--verbose", help="Show detailed errors.")] = False,
    no_color: Annotated[bool, typer.Option("--no-color", help="Disable Rich colors.")] = False,
    version: Annotated[bool, typer.Option("--version", help="Show version.")] = False,
) -> None:
    if version:
        _stdout.print(f"docstrans {__version__}")
        raise typer.Exit()

    _state.verbose = verbose
    _state.no_color = no_color

    try:
        cfg = load_config(
            config_path=config_path,
            db_path=db_path,
            base_url=base_url,
            api_key=api_key,
            timeout=timeout,
        )
    except DocstransError as e:
        _stderr.print(f"[bold red]Config error:[/bold red] {e.message}")
        raise typer.Exit(code=EXIT_CONFIG) from None

    _state.config = cfg
    setup_logging(cfg.log_path, verbose=verbose)

    if ctx.invoked_subcommand is None:
        _stdout.print(ctx.get_help())


# ── 1. translate-text ────────────────────────────────────────────────────────


@app.command("translate-text")
def translate_text(
    text: Annotated[str, typer.Argument(help="Text to translate.")],
    source: Annotated[str, typer.Option("--source", "-s", help="Source language (auto).")] = "auto",
    target: Annotated[str | None, typer.Option("--target", "-t", help="Target language.")] = None,
    fmt: Annotated[FormatEnum, typer.Option("--format", help="Text format.")] = FormatEnum.text,
    output: Annotated[
        Path | None, typer.Option("--output", "-o", help="Save translation to file.")
    ] = None,
    no_save: Annotated[bool, typer.Option("--no-save", help="Do not save to history.")] = False,
    json_out: Annotated[bool, typer.Option("--json", help="Output JSON.")] = False,
) -> None:
    """Translate a text string via REST API."""
    if not text.strip():
        _stderr.print("[bold red]Error:[/bold red] TEXT cannot be empty.")
        raise typer.Exit(code=2)

    cfg = _get_config()
    tgt = target or cfg.default_target

    try:
        conn = _init_db(cfg)
        client = _make_client(cfg)
        from docstrans.services.translation_service import translate_text as _translate

        result = _translate(
            client=client,
            conn=conn,
            text=text,
            source=source,
            target=tgt,
            fmt=fmt.value,
            save=not no_save,
        )
    except DocstransError as e:
        _handle_error(e, _state.verbose)
        return
    except Exception as e:
        _handle_error(e, _state.verbose)
        return

    if json_out:
        import json

        print(
            json.dumps(
                {
                    "source_language": result.source_lang,
                    "target_language": result.target_lang,
                    "translated_text": result.translated_text,
                    "provider": "libretranslate",
                    "saved_to_history": result.saved_to_history,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        _stdout.print(result.translated_text)

    if output:
        try:
            output.write_text(result.translated_text, encoding="utf-8")
            _stderr.print(f"Saved to: {output}")
        except OSError as e:
            _handle_error(FileError(str(e)), _state.verbose)


# ── 2. translate-file ────────────────────────────────────────────────────────


@app.command("translate-file")
def translate_file(
    input_path: Annotated[Path, typer.Argument(help="Path to input file.")],
    source: Annotated[str, typer.Option("--source", "-s", help="Source language.")] = "auto",
    target: Annotated[str | None, typer.Option("--target", "-t", help="Target language.")] = None,
    output: Annotated[Path | None, typer.Option("--output", "-o", help="Output file path.")] = None,
    overwrite: Annotated[
        bool, typer.Option("--overwrite", help="Overwrite existing output.")
    ] = False,
    create_dirs: Annotated[
        bool, typer.Option("--create-dirs", help="Create output parent dirs.")
    ] = False,
    encoding: Annotated[str, typer.Option("--encoding", help="File encoding.")] = "utf-8",
    fmt: Annotated[FormatEnum, typer.Option("--format", help="Text format.")] = FormatEnum.text,
    chunk_size: Annotated[
        int,
        typer.Option("--chunk-size", min=500, max=10000, help="Max segment chars."),
    ] = DEFAULT_CHUNK_SIZE,
    batch_size: Annotated[
        int,
        typer.Option("--batch-size", min=1, max=50, help="Max segments per request."),
    ] = DEFAULT_BATCH_SIZE,
    preserve_markdown_code: Annotated[
        bool,
        typer.Option("--preserve-markdown-code/--no-preserve-markdown-code"),
    ] = True,
    no_save: Annotated[bool, typer.Option("--no-save", help="Do not save to history.")] = False,
    json_out: Annotated[bool, typer.Option("--json", help="Output JSON summary.")] = False,
) -> None:
    """Translate a documentation file via REST API."""
    cfg = _get_config()
    tgt = target or cfg.default_target

    ext = input_path.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        _stderr.print(
            f"[yellow]Warning:[/yellow] extension {ext!r} is not officially "
            "supported; processing as plain text."
        )

    try:
        conn = _init_db(cfg)
        client = _make_client(cfg)
        from docstrans.services.file_service import translate_file as _tf

        result = _tf(
            client=client,
            conn=conn,
            input_path=input_path,
            source=source,
            target=tgt,
            output_path=output,
            overwrite=overwrite,
            create_dirs=create_dirs,
            encoding=encoding,
            fmt=fmt.value,
            chunk_size=chunk_size,
            batch_size=batch_size,
            preserve_markdown_code=preserve_markdown_code,
            save=not no_save,
        )
    except DocstransError as e:
        _handle_error(e, _state.verbose)
        return
    except Exception as e:
        _handle_error(e, _state.verbose)
        return

    if json_out:
        import json

        print(
            json.dumps(
                {
                    "input_path": result.input_path,
                    "output_path": result.output_path,
                    "source_language": result.source_lang,
                    "target_language": result.target_lang,
                    "segments_translated": result.segments_translated,
                    "provider": "libretranslate",
                    "saved_to_history": result.saved_to_history,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        _stdout.print(f"Translated file saved: {result.output_path}")
        _stdout.print(f"Segments translated: {result.segments_translated}")
        saved_str = "saved" if result.saved_to_history else "not saved"
        _stdout.print(f"History entry: {saved_str}")


# ── 3. detect-language ───────────────────────────────────────────────────────


@app.command("detect-language")
def detect_language(
    text: Annotated[str, typer.Argument(help="Text to detect language for.")],
    json_out: Annotated[bool, typer.Option("--json", help="Output raw JSON.")] = False,
) -> None:
    """Detect the language of a text string via REST API."""
    if not text.strip():
        _stderr.print("[bold red]Error:[/bold red] TEXT cannot be empty.")
        raise typer.Exit(code=2)

    cfg = _get_config()

    try:
        client = _make_client(cfg)
        results = client.detect(text)
    except DocstransError as e:
        _handle_error(e, _state.verbose)
        return
    except Exception as e:
        _handle_error(e, _state.verbose)
        return

    if not results:
        _stderr.print("[bold red]Error:[/bold red] No detection results.")
        raise typer.Exit(code=EXIT_INTERNAL)

    best = results[0]
    if json_out:
        import json

        print(
            json.dumps(
                {
                    "best": {"language": best.language, "confidence": best.confidence},
                    "detections": [
                        {"language": r.language, "confidence": r.confidence} for r in results
                    ],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        _stdout.print(f"Language: {best.language}")
        _stdout.print(f"Confidence: {best.confidence}")


# ── 4. languages-list ────────────────────────────────────────────────────────


@app.command("languages-list")
def languages_list(
    json_out: Annotated[bool, typer.Option("--json", help="Output JSON.")] = False,
    target_for: Annotated[
        str | None,
        typer.Option("--target-for", help="Filter targets for source lang."),
    ] = None,
) -> None:
    """List supported languages from the current API endpoint."""
    cfg = _get_config()

    try:
        client = _make_client(cfg)
        langs = client.languages()
    except DocstransError as e:
        _handle_error(e, _state.verbose)
        return
    except Exception as e:
        _handle_error(e, _state.verbose)
        return

    if target_for:
        for lang in langs:
            if lang.code == target_for:
                langs = [type(lang)(code=t, name=t, targets=[]) for t in lang.targets]
                break
        else:
            langs = []

    if json_out:
        import json

        print(
            json.dumps(
                [{"code": lg.code, "name": lg.name, "targets": lg.targets} for lg in langs],
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        from rich.table import Table

        table = Table(show_header=True, header_style="bold")
        table.add_column("Code")
        table.add_column("Name")
        table.add_column("Targets")
        for lang in langs:
            table.add_row(lang.code, lang.name, ", ".join(lang.targets[:8]))
        _stdout.print(table)


# ── 5. glossary-add ──────────────────────────────────────────────────────────


@app.command("glossary-add")
def glossary_add(
    source_term: Annotated[str, typer.Argument(help="Source language term.")],
    target_term: Annotated[str, typer.Argument(help="Target language term.")],
    source_lang: Annotated[
        str, typer.Option("--source-lang", "-s", help="Source language.")
    ] = "en",
    target_lang: Annotated[
        str, typer.Option("--target-lang", "-t", help="Target language.")
    ] = "ru",
    case_sensitive: Annotated[bool, typer.Option("--case-sensitive/--no-case-sensitive")] = False,
    note: Annotated[str | None, typer.Option("--note", help="Optional comment.")] = None,
    replace: Annotated[bool, typer.Option("--replace", help="Update if term exists.")] = False,
) -> None:
    """Add a term to the local glossary."""
    if not source_term.strip() or not target_term.strip():
        _stderr.print("[bold red]Error:[/bold red] Terms cannot be empty.")
        raise typer.Exit(code=2)

    cfg = _get_config()

    try:
        conn = _init_db(cfg)
        from docstrans.db.glossary_repo import add_term

        add_term(
            conn=conn,
            source_lang=source_lang,
            target_lang=target_lang,
            source_term=source_term,
            target_term=target_term,
            case_sensitive=case_sensitive,
            note=note,
            replace=replace,
        )
    except ConflictError as e:
        _stderr.print(f"[bold red]Error:[/bold red] {e.message}")
        raise typer.Exit(code=e.exit_code) from None
    except DocstransError as e:
        _handle_error(e, _state.verbose)
        return

    _stdout.print(
        f"Glossary term added: {source_term} -> {target_term} [{source_lang} -> {target_lang}]"
    )


# ── 6. glossary-list ─────────────────────────────────────────────────────────


@app.command("glossary-list")
def glossary_list(
    source_lang: Annotated[str | None, typer.Option("--source-lang", "-s")] = None,
    target_lang: Annotated[str | None, typer.Option("--target-lang", "-t")] = None,
    search: Annotated[str | None, typer.Option("--search")] = None,
    json_out: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """List local glossary terms."""
    cfg = _get_config()
    conn = _init_db(cfg)
    from docstrans.db.glossary_repo import list_terms

    terms = list_terms(conn, source_lang=source_lang, target_lang=target_lang, search=search)

    if not terms:
        _stdout.print("No glossary terms found.")
        return

    if json_out:
        import json

        print(
            json.dumps(
                [
                    {
                        "id": t.id,
                        "source_term": t.source_term,
                        "target_term": t.target_term,
                        "source_lang": t.source_lang,
                        "target_lang": t.target_lang,
                        "case_sensitive": t.case_sensitive,
                        "note": t.note,
                    }
                    for t in terms
                ],
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        from rich.table import Table

        table = Table(show_header=True, header_style="bold")
        table.add_column("ID")
        table.add_column("Source term")
        table.add_column("Target term")
        table.add_column("Langs")
        table.add_column("Case sensitive")
        for t in terms:
            table.add_row(
                str(t.id),
                t.source_term,
                t.target_term,
                f"{t.source_lang}->{t.target_lang}",
                "yes" if t.case_sensitive else "no",
            )
        _stdout.print(table)


# ── 7. glossary-remove ───────────────────────────────────────────────────────


@app.command("glossary-remove")
def glossary_remove(
    source_term: Annotated[str, typer.Argument(help="Source term to remove.")],
    source_lang: Annotated[str, typer.Option("--source-lang", "-s")] = "en",
    target_lang: Annotated[str, typer.Option("--target-lang", "-t")] = "ru",
) -> None:
    """Remove a term from the local glossary."""
    cfg = _get_config()
    conn = _init_db(cfg)
    from docstrans.db.glossary_repo import remove_term

    removed = remove_term(
        conn,
        source_term=source_term,
        source_lang=source_lang,
        target_lang=target_lang,
    )

    if not removed:
        _stdout.print("Glossary term not found.")
        raise typer.Exit(code=EXIT_NOT_FOUND)

    _stdout.print(f"Glossary term removed: {source_term} [{source_lang} -> {target_lang}]")


# ── 8. history-list ──────────────────────────────────────────────────────────


@app.command("history-list")
def history_list(
    limit: Annotated[int, typer.Option("--limit", min=1, max=500)] = 20,
    source_lang: Annotated[str | None, typer.Option("--source-lang", "-s")] = None,
    target_lang: Annotated[str | None, typer.Option("--target-lang", "-t")] = None,
    kind: Annotated[KindEnum | None, typer.Option("--kind")] = None,
    json_out: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Show translation history."""
    cfg = _get_config()
    conn = _init_db(cfg)
    from docstrans.db.history_repo import list_entries

    entries = list_entries(
        conn,
        limit=limit,
        source_lang=source_lang,
        target_lang=target_lang,
        kind=kind.value if kind else None,
    )

    if not entries:
        _stdout.print("No translation history found.")
        return

    if json_out:
        import json

        def _preview(t: str | None) -> str:
            return (t or "")[:80].replace("\n", " ")

        print(
            json.dumps(
                [
                    {
                        "id": e.id,
                        "created_at": e.created_at,
                        "kind": e.kind,
                        "source_lang": e.source_lang,
                        "target_lang": e.target_lang,
                        "source_preview": _preview(e.source_text),
                        "result_preview": _preview(e.translated_text),
                    }
                    for e in entries
                ],
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        from rich.table import Table

        table = Table(show_header=True, header_style="bold")
        table.add_column("ID")
        table.add_column("Created at")
        table.add_column("Kind")
        table.add_column("Langs")
        table.add_column("Source preview")
        table.add_column("Result preview")

        def _prev(t: str | None, n: int = 30) -> str:
            s = (t or "").replace("\n", " ")
            return s[:n] + "..." if len(s) > n else s

        for e in entries:
            table.add_row(
                str(e.id),
                e.created_at,
                e.kind,
                f"{e.source_lang}->{e.target_lang}",
                _prev(e.source_text),
                _prev(e.translated_text),
            )
        _stdout.print(table)


# ── 9. export-history ────────────────────────────────────────────────────────


@app.command("export-history")
def export_history(
    output_path: Annotated[Path, typer.Argument(help="Output file path.")],
    fmt: Annotated[ExportFormatEnum | None, typer.Option("--format", help="Export format.")] = None,
    limit: Annotated[int | None, typer.Option("--limit", min=1)] = None,
    source_lang: Annotated[str | None, typer.Option("--source-lang", "-s")] = None,
    target_lang: Annotated[str | None, typer.Option("--target-lang", "-t")] = None,
    overwrite: Annotated[bool, typer.Option("--overwrite")] = False,
    create_dirs: Annotated[bool, typer.Option("--create-dirs")] = False,
) -> None:
    """Export translation history to a file."""
    # Determine format from extension if not provided
    if fmt is None:
        ext = output_path.suffix.lower().lstrip(".")
        resolved_fmt = ext if ext in ("json", "csv", "md") else "json"
    else:
        resolved_fmt = fmt.value

    cfg = _get_config()
    conn = _init_db(cfg)
    from docstrans.db.history_repo import list_entries
    from docstrans.services.export_service import export_history as _export

    entries = list_entries(
        conn,
        limit=limit or 999_999,
        source_lang=source_lang,
        target_lang=target_lang,
    )

    try:
        _export(
            entries, output_path, fmt=resolved_fmt, overwrite=overwrite, create_dirs=create_dirs
        )
    except FileError as e:
        _handle_error(e, _state.verbose)
        return

    _stdout.print(f"History exported: {output_path}")
    _stdout.print(f"Records exported: {len(entries)}")


# ── 10. config-set ───────────────────────────────────────────────────────────


@app.command("config-set")
def config_set(
    key: Annotated[ConfigKeyEnum, typer.Argument(help="Config key.")],
    value: Annotated[str, typer.Argument(help="Config value.")],
) -> None:
    """Write a setting to the local config file."""
    from docstrans.config import _validate_base_url, _validate_timeout

    cfg = _get_config()

    key_str = key.value
    stored_value: object = value

    try:
        if key_str == "base_url":
            stored_value = _validate_base_url(value)
        elif key_str == "timeout":
            stored_value = _validate_timeout(value)
        elif key_str == "api_key":
            if not value.strip():
                raise typer.BadParameter("api_key must not be empty.")
        elif key_str in ("default_source", "default_target"):
            if not value.strip():
                raise typer.BadParameter(f"{key_str} must not be empty.")
            if key_str == "default_target" and value == "auto":
                raise typer.BadParameter("default_target cannot be 'auto'.")
    except DocstransError as e:
        _handle_error(e, _state.verbose)
        return

    write_config_key(cfg.config_path, key_str, stored_value)

    display = "************" if key_str == "api_key" else str(stored_value)
    _stdout.print(f"Config updated: {key_str}={display}")


# ── 11. config-show ──────────────────────────────────────────────────────────


@app.command("config-show")
def config_show(
    show_secrets: Annotated[
        bool, typer.Option("--show-secrets", help="Show API key in full.")
    ] = False,
    json_out: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Show effective configuration (file + env + defaults)."""
    cfg = _get_config()
    sources = cfg._sources

    api_key_display = cfg.api_key if (show_secrets and cfg.api_key) else cfg.mask_api_key()

    rows = [
        ("base_url", cfg.base_url, sources.get("base_url", "default")),
        ("api_key", api_key_display, sources.get("api_key", "none")),
        ("default_source", cfg.default_source, sources.get("default_source", "default")),
        ("default_target", cfg.default_target, sources.get("default_target", "default")),
        ("timeout", str(cfg.timeout), sources.get("timeout", "default")),
        ("config_path", str(cfg.config_path), "computed"),
        ("db_path", str(cfg.db_path), "computed"),
        ("log_path", str(cfg.log_path), "computed"),
    ]

    if json_out:
        import json

        print(
            json.dumps(
                {k: {"value": v, "source": s} for k, v, s in rows},
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        from rich.table import Table

        table = Table(show_header=True, header_style="bold")
        table.add_column("Key")
        table.add_column("Value")
        table.add_column("Source")
        for k, v, s in rows:
            table.add_row(k, v, s)
        _stdout.print(table)


# ── 12. doctor ───────────────────────────────────────────────────────────────


@app.command("doctor")
def doctor(
    skip_api: Annotated[bool, typer.Option("--skip-api", help="Skip REST API check.")] = False,
    json_out: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Check local environment and API connectivity."""
    cfg = _get_config()
    results: dict[str, str] = {}

    # Config file
    try:
        if cfg.config_path.exists():
            results["Config file"] = "ok"
        else:
            results["Config file"] = "not found (will be created on first write)"
    except Exception as e:
        results["Config file"] = f"error: {e}"

    # Database
    try:
        conn = _init_db(cfg)
        conn.execute("SELECT 1")
        results["Database"] = "ok"
    except Exception as e:
        results["Database"] = f"error: {e}"

    # Log dir
    try:
        cfg.log_path.parent.mkdir(parents=True, exist_ok=True)
        results["Log file"] = "ok"
    except Exception as e:
        results["Log file"] = f"error: {e}"

    # API
    api_ok = True
    if not skip_api:
        try:
            client = _make_client(cfg)
            try:
                client.health()
                results["REST API"] = "ok"
            except Exception:
                # Fallback: try /languages
                try:
                    client.languages()
                    results["REST API"] = "ok (via /languages)"
                except Exception as e2:
                    results["REST API"] = f"error: {e2}"
                    api_ok = False
        except Exception as e:
            results["REST API"] = f"error: {e}"
            api_ok = False
    else:
        results["REST API"] = "skipped"

    results["Base URL"] = cfg.base_url

    if json_out:
        import json

        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for k, v in results.items():
            ok = v in ("ok", "skipped") or v.startswith("ok")
            color = "green" if ok else "red"
            _stdout.print(f"{k}: [{color}]{v}[/{color}]")

    if not api_ok:
        raise typer.Exit(code=EXIT_NETWORK)
