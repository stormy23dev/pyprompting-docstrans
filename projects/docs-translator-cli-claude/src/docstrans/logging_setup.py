"""Configure rotating file logging for docstrans."""

from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

from docstrans.constants import LOG_BACKUP_COUNT, LOG_MAX_BYTES

_LOG_FORMAT = "%(asctime)sZ %(levelname)s %(name)s %(message)s"
_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"


def setup_logging(log_path: Path, verbose: bool = False) -> None:
    level_name = os.environ.get("DOCSTRANS_LOG_LEVEL", "DEBUG" if verbose else "INFO")
    level = getattr(logging, level_name.upper(), logging.INFO)

    log_path.parent.mkdir(parents=True, exist_ok=True)

    handler = RotatingFileHandler(
        log_path,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT))
    handler.setLevel(level)

    root = logging.getLogger("docstrans")
    root.setLevel(level)
    if not root.handlers:
        root.addHandler(handler)
