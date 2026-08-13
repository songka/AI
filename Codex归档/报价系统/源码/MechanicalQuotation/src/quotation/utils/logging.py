"""Logging setup for the quotation system.

Provides a unified logging configuration with console and file output.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path


def setup_logging(
    level: str = "INFO",
    log_format: str = "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
    log_file: str | None = None,
) -> logging.Logger:
    """Configure root logger with console and optional file handler.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_format: Format string for log messages.
        log_file: Optional path to a log file.

    Returns:
        The root logger.
    """
    root_logger = logging.getLogger("quotation")
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Clear existing handlers to avoid duplicates on re-configuration
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper(), logging.INFO))
    console_formatter = logging.Formatter(log_format)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)  # File always gets DEBUG
        file_handler.setFormatter(console_formatter)
        root_logger.addHandler(file_handler)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get a child logger under the 'quotation' namespace."""
    return logging.getLogger(f"quotation.{name}")
