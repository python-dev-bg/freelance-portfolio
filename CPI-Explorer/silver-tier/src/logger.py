import logging
import sys

from .config import Settings

__all__ = []

def _setup_logger(env = "dev"):
    logger = logging.getLogger("app_logger")
    logger.handlers.clear()  # avoid duplicate handlers
    logger.setLevel(logging.DEBUG if env == "dev" else logging.WARNING)

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    

_setup_logger(env=Settings.ENV)