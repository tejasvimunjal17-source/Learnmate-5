"""
backend/logger_setup.py
------------------------
Centralized logging configuration used across the whole application.
Logs to console always, and to a rotating file under ./logs when writable
(e.g. local/dev). On read-only deployment filesystems, file logging is
skipped gracefully.
"""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def get_logger(name: str = "career_pathway") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        # Already configured (avoid duplicate handlers on Streamlit reruns)
        return logger

    logger.setLevel(logging.INFO)
    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(fmt)
    logger.addHandler(console_handler)

    try:
        log_dir = Path(__file__).parent.parent / "logs"
        log_dir.mkdir(exist_ok=True)
        file_handler = RotatingFileHandler(
            log_dir / "app.log", maxBytes=1_000_000, backupCount=3
        )
        file_handler.setFormatter(fmt)
        logger.addHandler(file_handler)
    except Exception:
        # Read-only filesystem (some cloud hosts) - console logging is enough
        pass

    logger.propagate = False
    return logger
