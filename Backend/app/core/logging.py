"""Production-grade logging configuration using Loguru."""

import sys
from pathlib import Path

from loguru import logger


def setup_logging(
    log_level: str = "INFO",
    log_dir: str = "logs",
    debug: bool = False,
) -> None:
    """
    Configure production-grade logging with Loguru.

    Args:
        log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR)
        log_dir: Directory for log files
        debug: Enable debug mode with verbose output
    """
    # Remove default handler
    logger.remove()

    # Console handler - colored for development, plain for production
    if debug:
        logger.add(
            sys.stderr,
            level="DEBUG",
            format=(
                "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                "<level>{message}</level> {extra}"
            ),
            colorize=True,
            backtrace=True,
            diagnose=True,
        )
    else:
        logger.add(
            sys.stderr,
            level=log_level,
            format=(
                "{time:YYYY-MM-DD HH:mm:ss} | "
                "{level: <8} | "
                "{name}:{function}:{line} | "
                "{message}"
            ),
            colorize=False,
        )

    # Create log directory
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # Application log file - rotates daily, keeps 30 days
    logger.add(
        log_path / "app_{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="30 days",
        compression="zip",
        level="DEBUG" if debug else log_level,
        format=(
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
            "{level: <8} | "
            "{name}:{function}:{line} | "
            "{message}"
        ),
        serialize=False,
    )

    # Error log file - separate file for errors only
    logger.add(
        log_path / "errors_{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="90 days",
        compression="zip",
        level="ERROR",
        format=(
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
            "{level: <8} | "
            "{name}:{function}:{line} | "
            "{message}"
        ),
        backtrace=True,
        diagnose=True,
    )

    logger.info("Logging configured", level=log_level, debug=debug)


def get_logger(name: str):
    """
    Get a logger instance with context binding.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance bound with name context
    """
    return logger.bind(name=name)
