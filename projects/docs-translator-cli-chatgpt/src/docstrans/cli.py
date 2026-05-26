from __future__ import annotations

import logging
from contextlib import suppress
from pathlib import Path
from typing import Annotated, Any

import typer
from rich.table import Table

from docstrans.api.client import LibreTranslateClient
from docstrans.config import build_config, mask_secret, write_config_value
from docstrans.db.connection import connect
from docstrans.db.glossary_repo import GlossaryRepo
from docstrans.db.history_repo import HistoryRepo
from docstrans.db.migrations import run_migrations
from docstrans.exceptions import DocstransError
from docstrans.logging_setup import setup_logging
from docstrans.services.detection_service import DetectionService
from docstrans.services.export_service import ExportService
from docstrans.services.file_service import FileTranslationService
from docstrans.services.history_service import HistoryService
from docstrans.services.translation_service import TranslationService
from docstrans.ui.output import make_console, preview, print_json

app = typer.Typer(no_args_is_help=True, add_completion=False, help="Docs Translator CLI")
logger = logging.getLogger("docstrans.cli")


class Runtime:
    def __init__(self, *, config, no_color: bool, verbose: bool) -> None:  # noqa: ANN001
        self.config = config
        self.no_color = no_color
        self.verbose = verbose
        self.console = make_console(no_color=no_color)
        self.err_console = make_console(no_color=no_color, stderr=True)
        self.conn = connect(config.db_path)
        self._closed = False
        run_migrations(self.conn)
        self.glossary_repo = GlossaryRepo(self.conn)
        self.history_repo = HistoryRepo(self.conn)
        self.client = LibreTranslateClient(
            base_url=config.base_url,
            api_key=config.api_key,
            timeout=config.timeout,
        )

    def close(self) -> None:
        if not self._closed:
            self.conn.close()
            self._closed = True

    def __del__(self) -> None:
        with suppress(Exception):
            self.close()


def _runtime(ctx: typer.Context) -> Runtime:
    runtime = ctx.obj
    if not isinstance(runtime, Runtime):
        raise RuntimeError("runtime is not initialized")
    return runtime


@app.callback()
def main(
    ctx: typer.Context,
    config_path: Annotated[
        Path | None, typer.Option("--config-path", help="Path to JSON config file.")
    ] = None,
    db_path: Annotated[
        Path | None, typer.Option("--db-path", help="Path to SQLite database.")
    ] = None,
    base_url: Annotated[
        str | None, typer.Option("--base-url", help="LibreTranslate API base URL.")
    ] = None,
    api_key: Annotated[str | None, typer.Option("--api-key", help="Translation API key.")] = None,
    timeout: Annotated[
        float | None, typer.Option("--timeout", help="HTTP timeout in seconds.")
    ] = None,
    verbose: Annotated[
        bool, typer.Option("--verbose", help="Enable verbose errors and debug logs.")
    ] = False,
    no_color: Annotated[bool, typer.Option("--no-color", help="Disable Rich colors.")] = False,
) -> None:
    try:
        config = build_config(
            config_path=config_path,
            db_path=db_path,
            base_url=base_url,
            api_key=api_key,
            timeout=timeout,
        )
        setup_logging(config.log_path, verbose=verbose)
        runtime = Runtime(config=config, no_color=no_color, verbose=verbose)
        ctx.obj = runtime
        ctx.call_on_close(runtime.close)
    except DocstransError as exc:
        console = make_console(no_color=no_color, stderr=True)
        console.print(str(exc), style="red")
        raise typer.Exit(exc.exit_code) from exc


def _handle_error(runtime: Runtime, exc: Exception) -> None:
    if isinstance(exc, DocstransError):
        runtime.err_console.print(str(exc), style="red")
        logger.exception("Command failed") if runtime.verbose else logger.error(
            "Command failed: %s", exc
        )
        raise typer.Exit(exc.exit_code) from exc
    runtime.err_console.print("Error: unexpected internal error.", style="red")
    logger.exception("Unexpected internal error")
    if runtime.verbose:
        runtime.err_console.print_exception()
    raise typer.Exit(20) from exc


def _validate_text(text: str) -> str:
    if not text:
        raise typer.BadParameter("Text cannot be empty.")
    return text


def _source_default(runtime: Runtime, source: str | None) -> str:
    return source or runtime.config.default_source


def _target_default(runtime: Runtime, target: str | None) -> str:
    return target or runtime.config.default_target


def _validate_range(value: int, *, min_value: int, max_value: int, name: str) -> int:
    if value < min_value or value > max_value:
        raise typer.BadParameter(f"{name} must be between {min_value} and {max_value}.")
    return value


@app.command("translate-text")
def translate_text_command(
    ctx: typer.Context,
    text: Annotated[str, typer.Argument(help="Text to translate.")],
    source: Annotated[str | None, typer.Option("--source", "-s", help="Source language.")] = None,
    target: Annotated[str | None, typer.Option("--target", "-t", help="Target language.")] = None,
    text_format: Annotated[
        str, typer.Option("--format", help="Text format: text or html.")
    ] = "text",
    output: Annotated[Path | None, typer.Option("--output", "-o", help="Output file.")] = None,
    no_save: Annotated[bool, typer.Option("--no-save", help="Do not save to history.")] = False,
    as_json: Annotated[bool, typer.Option("--json", help="Print JSON.")] = False,
) -> None:
    runtime = _runtime(ctx)
    try:
        _validate_text(text)
        if text_format not in {"text", "html"}:
            raise typer.BadParameter("format must be text or html")
        service = TranslationService(
            client=runtime.client,
            glossary_repo=runtime.glossary_repo,
            history_repo=runtime.history_repo,
            base_url=runtime.config.base_url,
        )
        result = service.translate_text(
            text,
            source=_source_default(runtime, source),
            target=_target_default(runtime, target),
            text_format=text_format,
            save=not no_save,
        )
        if output:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(result.translated_text, encoding="utf-8")
        if as_json:
            print_json(
                runtime.console,
                {
                    "source_language": result.source_language,
                    "target_language": result.target_language,
                    "translated_text": result.translated_text,
                    "provider": result.provider,
                    "saved_to_history": result.saved_to_history,
                },
            )
        else:
            runtime.console.print(result.translated_text)
    except Exception as exc:  # noqa: BLE001
        _handle_error(runtime, exc)


@app.command("translate-file")
def translate_file_command(
    ctx: typer.Context,
    input_path: Annotated[Path, typer.Argument(help="Input text file.")],
    source: Annotated[str | None, typer.Option("--source", "-s", help="Source language.")] = None,
    target: Annotated[str | None, typer.Option("--target", "-t", help="Target language.")] = None,
    output: Annotated[Path | None, typer.Option("--output", "-o", help="Output file.")] = None,
    overwrite: Annotated[bool, typer.Option("--overwrite", help="Overwrite output file.")] = False,
    create_dirs: Annotated[
        bool, typer.Option("--create-dirs", help="Create output directories.")
    ] = False,
    encoding: Annotated[
        str, typer.Option("--encoding", help="Input and output encoding.")
    ] = "utf-8",
    text_format: Annotated[
        str, typer.Option("--format", help="Text format: text or html.")
    ] = "text",
    chunk_size: Annotated[int, typer.Option("--chunk-size", help="Max segment size.")] = 4000,
    batch_size: Annotated[int, typer.Option("--batch-size", help="Max API batch size.")] = 20,
    preserve_markdown_code: Annotated[
        bool, typer.Option("--preserve-markdown-code/--translate-markdown-code")
    ] = True,
    no_save: Annotated[bool, typer.Option("--no-save", help="Do not save to history.")] = False,
    as_json: Annotated[bool, typer.Option("--json", help="Print JSON summary.")] = False,
) -> None:
    runtime = _runtime(ctx)
    try:
        if text_format not in {"text", "html"}:
            raise typer.BadParameter("format must be text or html")
        _validate_range(chunk_size, min_value=500, max_value=10000, name="chunk-size")
        _validate_range(batch_size, min_value=1, max_value=50, name="batch-size")
        if input_path.suffix.lower() not in {".txt", ".md", ".rst"}:
            runtime.err_console.print(
                f"Warning: extension {input_path.suffix} is not officially supported; "
                "processing as plain text."
            )
        service = FileTranslationService(
            client=runtime.client,
            glossary_repo=runtime.glossary_repo,
            history_repo=runtime.history_repo,
            base_url=runtime.config.base_url,
        )
        result = service.translate_file(
            input_path,
            output_path=output,
            source=_source_default(runtime, source),
            target=_target_default(runtime, target),
            text_format=text_format,
            chunk_size=chunk_size,
            batch_size=batch_size,
            preserve_markdown_code=preserve_markdown_code,
            encoding=encoding,
            overwrite=overwrite,
            create_dirs=create_dirs,
            save=not no_save,
        )
        if as_json:
            print_json(runtime.console, result.__dict__)
        else:
            runtime.console.print(f"Translated file saved: {result.output_path}")
            runtime.console.print(f"Segments translated: {result.segments_translated}")
            runtime.console.print(
                f"History entry: {'saved' if result.saved_to_history else 'not saved'}"
            )
    except Exception as exc:  # noqa: BLE001
        _handle_error(runtime, exc)


@app.command("detect-language")
def detect_language_command(
    ctx: typer.Context,
    text: Annotated[str, typer.Argument(help="Text to detect.")],
    as_json: Annotated[bool, typer.Option("--json", help="Print JSON.")] = False,
) -> None:
    runtime = _runtime(ctx)
    try:
        _validate_text(text)
        result = DetectionService(runtime.client).detect(text)
        if as_json:
            print_json(runtime.console, result)
        else:
            best = result["best"]
            runtime.console.print(f"Language: {best.get('language')}")
            runtime.console.print(f"Confidence: {best.get('confidence')}")
    except Exception as exc:  # noqa: BLE001
        _handle_error(runtime, exc)


@app.command("languages-list")
def languages_list_command(
    ctx: typer.Context,
    as_json: Annotated[bool, typer.Option("--json", help="Print JSON.")] = False,
    target_for: Annotated[
        str | None, typer.Option("--target-for", help="Show targets for source.")
    ] = None,
) -> None:
    runtime = _runtime(ctx)
    try:
        languages, _, _ = runtime.client.languages()
        if target_for:
            selected = next((item for item in languages if item.get("code") == target_for), None)
            languages = [
                {"code": code, "name": code, "targets": []}
                for code in (selected or {}).get("targets", [])
            ]
        if as_json:
            print_json(runtime.console, languages)
            return
        table = Table()
        table.add_column("Code")
        table.add_column("Name")
        table.add_column("Targets")
        for item in languages:
            table.add_row(
                str(item.get("code", "")),
                str(item.get("name", "")),
                ", ".join(item.get("targets", []) or []),
            )
        runtime.console.print(table)
    except Exception as exc:  # noqa: BLE001
        _handle_error(runtime, exc)


@app.command("glossary-add")
def glossary_add_command(
    ctx: typer.Context,
    source_term: Annotated[str, typer.Argument(help="Source term.")],
    target_term: Annotated[str, typer.Argument(help="Target term.")],
    source_lang: Annotated[str, typer.Option("--source-lang", "-s")] = "en",
    target_lang: Annotated[str, typer.Option("--target-lang", "-t")] = "ru",
    case_sensitive: Annotated[bool, typer.Option("--case-sensitive")] = False,
    note: Annotated[str | None, typer.Option("--note")] = None,
    replace: Annotated[bool, typer.Option("--replace")] = False,
) -> None:
    runtime = _runtime(ctx)
    try:
        runtime.glossary_repo.add(
            source_term=source_term,
            target_term=target_term,
            source_lang=source_lang,
            target_lang=target_lang,
            case_sensitive=case_sensitive,
            note=note,
            replace=replace,
        )
        action = "updated" if replace else "added"
        runtime.console.print(
            f"Glossary term {action}: {source_term} -> {target_term} "
            f"[{source_lang} -> {target_lang}]"
        )
    except Exception as exc:  # noqa: BLE001
        _handle_error(runtime, exc)


@app.command("glossary-list")
def glossary_list_command(
    ctx: typer.Context,
    source_lang: Annotated[str | None, typer.Option("--source-lang", "-s")] = None,
    target_lang: Annotated[str | None, typer.Option("--target-lang", "-t")] = None,
    search: Annotated[str | None, typer.Option("--search")] = None,
    as_json: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    runtime = _runtime(ctx)
    try:
        rows = runtime.glossary_repo.list(
            source_lang=source_lang, target_lang=target_lang, search=search
        )
        if as_json:
            print_json(runtime.console, rows)
            return
        if not rows:
            runtime.console.print("No glossary terms found.")
            return
        table = Table()
        table.add_column("ID")
        table.add_column("Source term")
        table.add_column("Target term")
        table.add_column("Langs")
        table.add_column("Case sensitive")
        for row in rows:
            table.add_row(
                str(row["id"]),
                row["source_term"],
                row["target_term"],
                f"{row['source_lang']}->{row['target_lang']}",
                "yes" if row["case_sensitive"] else "no",
            )
        runtime.console.print(table)
    except Exception as exc:  # noqa: BLE001
        _handle_error(runtime, exc)


@app.command("glossary-remove")
def glossary_remove_command(
    ctx: typer.Context,
    source_term: Annotated[str, typer.Argument(help="Source term to remove.")],
    source_lang: Annotated[str, typer.Option("--source-lang", "-s")] = "en",
    target_lang: Annotated[str, typer.Option("--target-lang", "-t")] = "ru",
) -> None:
    runtime = _runtime(ctx)
    try:
        runtime.glossary_repo.remove(
            source_term=source_term, source_lang=source_lang, target_lang=target_lang
        )
        runtime.console.print(
            f"Glossary term removed: {source_term} [{source_lang} -> {target_lang}]"
        )
    except Exception as exc:  # noqa: BLE001
        _handle_error(runtime, exc)


@app.command("history-list")
def history_list_command(
    ctx: typer.Context,
    limit: Annotated[int, typer.Option("--limit")] = 20,
    source_lang: Annotated[str | None, typer.Option("--source-lang", "-s")] = None,
    target_lang: Annotated[str | None, typer.Option("--target-lang", "-t")] = None,
    kind: Annotated[str | None, typer.Option("--kind")] = None,
    as_json: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    runtime = _runtime(ctx)
    try:
        _validate_range(limit, min_value=1, max_value=500, name="limit")
        if kind and kind not in {"text", "file"}:
            raise typer.BadParameter("kind must be text or file")
        rows = HistoryService(runtime.history_repo).list(
            limit=limit, source_lang=source_lang, target_lang=target_lang, kind=kind
        )
        if as_json:
            print_json(runtime.console, rows)
            return
        if not rows:
            runtime.console.print("No translation history found.")
            return
        table = Table()
        table.add_column("ID")
        table.add_column("Created at")
        table.add_column("Kind")
        table.add_column("Langs")
        table.add_column("Source preview")
        table.add_column("Result preview")
        for row in rows:
            table.add_row(
                str(row["id"]),
                row["created_at"],
                row["kind"],
                f"{row['source_lang']}->{row['target_lang']}",
                preview(row.get("source_text")),
                preview(row.get("translated_text")),
            )
        runtime.console.print(table)
    except Exception as exc:  # noqa: BLE001
        _handle_error(runtime, exc)


@app.command("export-history")
def export_history_command(
    ctx: typer.Context,
    output_path: Annotated[Path, typer.Argument(help="Export output file.")],
    export_format: Annotated[str | None, typer.Option("--format", help="json, csv, or md.")] = None,
    limit: Annotated[int | None, typer.Option("--limit")] = None,
    source_lang: Annotated[str | None, typer.Option("--source-lang", "-s")] = None,
    target_lang: Annotated[str | None, typer.Option("--target-lang", "-t")] = None,
    overwrite: Annotated[bool, typer.Option("--overwrite")] = False,
    create_dirs: Annotated[bool, typer.Option("--create-dirs")] = False,
) -> None:
    runtime = _runtime(ctx)
    try:
        if export_format and export_format not in {"json", "csv", "md"}:
            raise typer.BadParameter("format must be json, csv, or md")
        if limit is not None:
            _validate_range(limit, min_value=1, max_value=500000, name="limit")
        count = ExportService(runtime.history_repo).export(
            output_path,
            export_format=export_format,
            limit=limit,
            source_lang=source_lang,
            target_lang=target_lang,
            overwrite=overwrite,
            create_dirs=create_dirs,
        )
        runtime.console.print(f"History exported: {output_path}")
        runtime.console.print(f"Records exported: {count}")
    except Exception as exc:  # noqa: BLE001
        _handle_error(runtime, exc)


@app.command("config-set")
def config_set_command(
    ctx: typer.Context,
    key: Annotated[str, typer.Argument(help="Config key.")],
    value: Annotated[str, typer.Argument(help="Config value.")],
) -> None:
    runtime = _runtime(ctx)
    try:
        updated_key, validated = write_config_value(runtime.config.config_path, key, value)
        shown = mask_secret(str(validated)) if updated_key == "api_key" else str(validated)
        runtime.console.print(f"Config updated: {updated_key}={shown}")
    except Exception as exc:  # noqa: BLE001
        _handle_error(runtime, exc)


@app.command("config-show")
def config_show_command(
    ctx: typer.Context,
    show_secrets: Annotated[bool, typer.Option("--show-secrets")] = False,
    as_json: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    runtime = _runtime(ctx)
    config = runtime.config
    values: list[tuple[str, Any, str]] = [
        ("base_url", config.base_url, config.sources.get("base_url", "computed")),
        (
            "api_key",
            config.api_key if show_secrets else mask_secret(config.api_key),
            config.sources.get("api_key", "none") if config.api_key else "none",
        ),
        ("default_source", config.default_source, config.sources.get("default_source", "default")),
        ("default_target", config.default_target, config.sources.get("default_target", "default")),
        ("timeout", config.timeout, config.sources.get("timeout", "default")),
        ("config_path", str(config.config_path), "computed"),
        ("db_path", str(config.db_path), "computed"),
        ("log_path", str(config.log_path), "computed"),
    ]
    if as_json:
        print_json(
            runtime.console,
            {key: {"value": value, "source": source} for key, value, source in values},
        )
        return
    table = Table()
    table.add_column("Key")
    table.add_column("Value")
    table.add_column("Source")
    for key, value, source in values:
        table.add_row(key, str(value), source)
    runtime.console.print(table)


@app.command("doctor")
def doctor_command(
    ctx: typer.Context,
    skip_api: Annotated[bool, typer.Option("--skip-api")] = False,
    as_json: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    runtime = _runtime(ctx)
    checks: dict[str, str] = {}
    api_exit = 0
    checks["config_file"] = (
        "ok" if runtime.config.config_path.parent.exists() else "missing directory"
    )
    try:
        runtime.conn.execute("SELECT 1").fetchone()
        checks["database"] = "ok"
    except Exception:  # noqa: BLE001
        checks["database"] = "error"
    try:
        runtime.config.log_path.parent.mkdir(parents=True, exist_ok=True)
        checks["log_file"] = "ok"
    except OSError:
        checks["log_file"] = "error"
    if skip_api:
        checks["rest_api"] = "skipped"
    else:
        try:
            runtime.client.health()
            checks["rest_api"] = "ok"
        except DocstransError:
            try:
                runtime.client.languages()
                checks["rest_api"] = "ok"
            except DocstransError as exc:
                checks["rest_api"] = str(exc)
                api_exit = 10
    if as_json:
        print_json(runtime.console, {**checks, "base_url": runtime.config.base_url})
    else:
        runtime.console.print(f"Config file: {checks['config_file']}")
        runtime.console.print(f"Database: {checks['database']}")
        runtime.console.print(f"Log file: {checks['log_file']}")
        runtime.console.print(f"REST API: {checks['rest_api']}")
        runtime.console.print(f"Base URL: {runtime.config.base_url}")
    if api_exit:
        raise typer.Exit(api_exit)


if __name__ == "__main__":
    app()
