"""Shared logging module."""

import logging
import os
from datetime import datetime, timedelta
from pathlib import Path

import config

LOG_DIR = os.path.join(config.DATA_DIR, "logs")
LOG_RETENTION_DAYS = 30
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logger(name: str = "monitor") -> logging.Logger:
    """Configure and return a logger instance.

    Args:
        name: Logger name

    Returns:
        Configured Logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger

    Path(LOG_DIR).mkdir(parents=True, exist_ok=True)

    log_file = os.path.join(
        LOG_DIR, f"monitor_{datetime.now().strftime('%Y-%m-%d')}.log"
    )
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    logger.addHandler(console_handler)

    return logger


def cleanup_old_logs():
    """Remove log files older than retention period."""
    log_path = Path(LOG_DIR)
    if not log_path.exists():
        return

    cutoff_date = datetime.now() - timedelta(days=LOG_RETENTION_DAYS)
    for log_file in log_path.glob("monitor_*.log"):
        try:
            date_str = log_file.stem.split("_")[-1]
            file_date = datetime.strptime(date_str, "%Y-%m-%d")
            if file_date < cutoff_date:
                log_file.unlink()
        except (ValueError, IndexError):
            continue