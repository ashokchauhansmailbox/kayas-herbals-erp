import logging
import sys

import structlog
from .config import get_settings

def configure_logging() -> None:
    s = get_settings()
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=s.LOG_LEVEL)
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    processors.append(
        structlog.processors.JSONRenderer() if s.APP_ENV != "dev"
        else structlog.dev.ConsoleRenderer()
    )
    structlog.configure(processors=processors, wrapper_class=structlog.make_filtering_bound_logger(logging.INFO))

log = structlog.get_logger()
