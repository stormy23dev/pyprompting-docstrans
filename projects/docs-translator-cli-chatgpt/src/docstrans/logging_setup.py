from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(log_path: Path, *, verbose: bool = False) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    env_level = os.getenv("DOCSTRANS_LOG_LEVEL", "").upper()
    level = logging.DEBUG if verbose else getattr(logging, env_level, logging.INFO)

    root = logging.getLogger("docstrans")
    root.setLevel(level)
    root.handlers.clear()

    handler = RotatingFileHandler(
        log_path,
        maxBytes=1_048_576,
        backupCount=3,
        encoding="utf-8",
    )
    handler.setLevel(level)
    formatter = logging.Formatter(
        fmt="%(asctime)sZ %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    handler.setFormatter(formatter)
    root.addHandler(handler)
    root.propagate = False
