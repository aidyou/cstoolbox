import logging
import os
from .config.config import log_level, log_dir


def get_logger(name):
    """Get a logger with the given name and configure it for logging."""
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    level_dict = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
    }
    level = level_dict.get(log_level, logging.INFO)

    # Configure logging
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        filename=os.path.join(log_dir, "csbot.log"),
    )

    return logging.getLogger(name)
