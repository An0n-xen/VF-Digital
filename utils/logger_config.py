import os
import logging
import colorlog

def setup_logger(name=None, level=logging.INFO):
    """
    Set up logger with file and line number information.

    Args:
        name: Logger name (use __name__ to get module name)
        level: Logging level (DEBUG, INFO, WARNING, ERROR)

    Returns:
        logger: Configured logger instance
    """

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent duplicated handers
    if logger.handlers:
        return logger

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)

   # Colored formatter
    console_formatter = colorlog.ColoredFormatter(
        fmt="%(log_color)s%(asctime)s | %(filename)s:%(lineno)d | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "white",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        },
    )

    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    return logger