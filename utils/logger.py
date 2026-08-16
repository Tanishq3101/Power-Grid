"""
===============================================================================
Project : Multi-Agent Reinforcement Learning for Smart Power Grid Control
File    : utils/logger.py

Description
-----------
Centralized logging configuration for the project.

Every module calls:

    from utils.logger import get_logger
    logger = get_logger(__name__)

instead of configuring its own logger. This keeps log formatting
consistent across env/, config/, agents/, baselines/, evaluation/,
and training/.

Logs are written to both the console and a rotating file under
LOG_DIRECTORY (see config/constants.py).
===============================================================================
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# -----------------------------------------------------------------------------
# Log directory (kept local to avoid a circular import with config.constants)
# -----------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_LOG_DIRECTORY = _PROJECT_ROOT / "logs"
_LOG_DIRECTORY.mkdir(parents=True, exist_ok=True)

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_DEFAULT_LEVEL = logging.INFO

_configured_loggers: dict[str, logging.Logger] = {}


def get_logger(name: str, level: int = _DEFAULT_LEVEL) -> logging.Logger:
    """
    Return a configured logger for the given module name.

    Parameters
    ----------
    name : str
        Usually ``__name__`` of the calling module.

    level : int, optional
        Logging level (default: logging.INFO).

    Returns
    -------
    logging.Logger
        A logger writing to both console and a shared log file.

    Notes
    -----
    Safe to call multiple times with the same name — handlers are
    only attached once per logger to avoid duplicate log lines.
    """

    if name in _configured_loggers:
        return _configured_loggers[name]

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (shared log file for the whole project)
    file_handler = logging.FileHandler(
        _LOG_DIRECTORY / "power_grid_marl.log",
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    _configured_loggers[name] = logger

    return logger
