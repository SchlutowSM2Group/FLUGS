"""Logging helpers for FLUGS."""

import logging as _logging
from datetime import datetime
from pathlib import Path


def setup_logging(
    namespace: str | None = None,
    level: int | str | None = None,
    format_string: str | None = None,
    log_file: str | None = None,
    log_dir: str | Path = "logs",
    auto_file: bool = True,
    run_name: str | None = None,
) -> _logging.Logger:
    """Set up logging with console and optional file handlers.

    Parameters
    ----------
    namespace : str, optional
        Logger namespace. Defaults to ``"flugs"``.
    level : int or str, optional
        Logging level. Defaults to ``INFO``.
    format_string : str, optional
        Custom format string. Defaults to a timestamped format.
    log_file : str, optional
        Explicit log filename. Overrides *auto_file*.
    log_dir : str or Path
        Directory for log files. Created if missing.
    auto_file : bool
        If True and *log_file* is None, generate a timestamped filename.
    run_name : str, optional
        Optional name to include in the auto-generated filename.

    Returns
    -------
    logging.Logger
    """
    if namespace is None:
        namespace = "flugs"
    if level is None:
        level = _logging.INFO
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    handlers: list[_logging.Handler] = [_logging.StreamHandler()]

    if auto_file and log_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = (
            f"{namespace}_{run_name}_{timestamp}.log"
            if run_name
            else f"{namespace}_{timestamp}.log"
        )

    if log_file:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        handlers.append(_logging.FileHandler(log_path / log_file))

    _logging.basicConfig(
        level=level,
        format=format_string,
        handlers=handlers,
        force=True,
    )

    logger = _logging.getLogger(namespace)
    logger.setLevel(level)

    if log_file:
        logger.info("Logging initialized — writing to: %s", Path(log_dir) / log_file)

    return logger
