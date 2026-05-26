from __future__ import annotations

from docstrans.services.glossary_service import apply_glossary, restore_glossary


def test_glossary_add_list_remove(runner, cli_base):
    app = app_import()
    add = runner.invoke(
        app,
        [
            *cli_base,
            "glossary-add",
            "deployment pipeline",
            "конвейер",
            "--source-lang",
            "en",
            "--target-lang",
            "ru",
        ],
    )
    assert add.exit_code == 0, add.output
    listed = runner.invoke(
        app, [*cli_base, "glossary-list", "--source-lang", "en", "--target-lang", "ru"]
    )
    assert listed.exit_code == 0, listed.output
    assert "deployment pipeline" in listed.output
    removed = runner.invoke(
        app,
        [
            *cli_base,
            "glossary-remove",
            "deployment pipeline",
            "--source-lang",
            "en",
            "--target-lang",
            "ru",
        ],
    )
    assert removed.exit_code == 0, removed.output
    listed_empty = runner.invoke(app, [*cli_base, "glossary-list"])
    assert "No glossary terms found" in listed_empty.output


def test_glossary_duplicate_without_replace_fails(runner, cli_base):
    app = app_import()
    assert runner.invoke(app, [*cli_base, "glossary-add", "pull request", "запрос"]).exit_code == 0
    duplicate = runner.invoke(app, [*cli_base, "glossary-add", "pull request", "запрос"])
    assert duplicate.exit_code == 6


def test_glossary_replaces_longest_term_first():
    terms = [
        {"source_term": "deployment", "target_term": "развертывание", "case_sensitive": 0},
        {
            "source_term": "deployment pipeline",
            "target_term": "конвейер развертывания",
            "case_sensitive": 0,
        },
    ]
    applied = apply_glossary("deployment pipeline deployment", terms)
    restored = restore_glossary(applied.text, applied.placeholders)
    assert restored == "конвейер развертывания развертывание"


def app_import():
    from docstrans.cli import app

    return app
