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
    # Suppress 'Dropping a patch' warnings at the handler level
    class BokehPatchFilter(logging.Filter):
        def filter(self, record):
            return "Dropping a patch because it contains a previously known reference" not in record.getMessage()
    handler.addFilter(BokehPatchFilter())
    # Suppress 'Dropping a patch' warnings globally at the root logger
    class GlobalBokehPatchFilter(logging.Filter):
        def filter(self, record):
            return "Dropping a patch because it contains a previously known reference" not in record.getMessage()
    logging.getLogger().addFilter(GlobalBokehPatchFilter())
    # Suppress noisy Bokeh logs
    for name in [
        "bokeh", 
        "bokeh.document", 
        "bokeh.core", 
        "bokeh.server",
        "tornado.application"
    ]:
        logging.getLogger(name).setLevel(logging.ERROR)
    

_setup_logger(env=Settings.ENV)