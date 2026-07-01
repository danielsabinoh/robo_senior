"""Logging setup for seniorbot executions."""

from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path


def project_root() -> Path:
    """Return the stable folder used for local logs and run outputs."""

    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def default_log_dir() -> Path:
    """Return the default log directory for the project/app folder."""

    return project_root() / "logs"


def configure_run_logging(
    *,
    level: int = logging.INFO,
    log_dir: str | Path | None = None,
    run_name: str = "seniorbot",
) -> Path:
    """Configure console and persistent file logging for one run."""

    target_dir = Path(log_dir) if log_dir is not None else default_log_dir()
    target_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_path = target_dir / f"{run_name}-{timestamp}.log"

    root_logger = logging.getLogger()
    reset_logging_handlers()

    root_logger.setLevel(level)
    formatter = logging.Formatter(
        fmt="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    logging.getLogger("seniorbot").info("Log iniciado: %s", log_path)
    return log_path


def shutdown_logging() -> None:
    """Flush and close all logging handlers."""

    reset_logging_handlers()
    logging.shutdown()


def reset_logging_handlers() -> None:
    """Remove and close handlers from the root logger."""

    root_logger = logging.getLogger()
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)
        handler.close()
