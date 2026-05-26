"""Shared test fixtures."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from docstrans.db.connection import get_connection
from docstrans.db.migrations import apply_migrations


@pytest.fixture
def tmp_db(tmp_path: Path) -> sqlite3.Connection:
    """Return a fresh in-memory-ish SQLite connection with schema applied."""
    db_path = tmp_path / "test.sqlite3"
    conn = get_connection(db_path)
    apply_migrations(conn)
    return conn


@pytest.fixture
def tmp_config_path(tmp_path: Path) -> Path:
    return tmp_path / "config.json"


@pytest.fixture
def tmp_db_path(tmp_path: Path) -> Path:
    return tmp_path / "test.sqlite3"
