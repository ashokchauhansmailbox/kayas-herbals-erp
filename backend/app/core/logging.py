import logging
import sys
from typing import Any

import structlog

from .config import get_settings


def configure_logging() -> None:
    s = get_settings()
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=s.LOG_LEVEL)
    processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]
    if s.APP_ENV == "dev":
        # ConsoleRenderer already formats exception info in a pretty way; skipping
        # format_exc_info avoids the structlog "remove format_exc_info from
        # processor chain" warning while keeping tracebacks readable.
        processors.append(structlog.dev.ConsoleRenderer())
    else:
        processors.append(structlog.processors.format_exc_info)
        processors.append(structlog.processors.JSONRenderer())
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    )


log = structlog.get_logger()
