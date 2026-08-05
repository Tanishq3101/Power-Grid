"""
===============================================================================
Project : Multi-Agent Reinforcement Learning for Smart Power Grid Control
File    : logger.py
Author  : Tanishq Vijay
Created : Day 2

Description
-----------
Provides a centralized logging utility for the project.

Instead of using print() statements throughout the codebase,
every module should use the project logger.

Features
--------
• Console logging
• File logging
• Automatic log directory creation
• Timestamped messages
• Configurable log level

Example
-------
from utils.logger import get_logger

logger = get_logger(__name__)

logger.info("Power flow converged successfully.")
logger.warning("Voltage limit exceeded.")
logger.error("Power flow failed.")

===============================================================================
"""

from __future__ import annotations

import logging
from pathlib import Path

from config.constants import LOG_DIRECTORY


def get_logger(name: str) -> logging.Logger:
    """
    Create and return a configured logger.

    Parameters
    ----------
    name : str
        Usually pass __name__ from the calling module.

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """

    # Create logs directory if it doesn't exist
    Path(LOG_DIRECTORY).mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # -------------------------------------------------------------------------
    # Console Handler
    # -------------------------------------------------------------------------

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # -------------------------------------------------------------------------
    # File Handler
    # -------------------------------------------------------------------------

    log_file = Path(LOG_DIRECTORY) / "power_grid.log"

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    logger.propagate = False

    return logger