"""Structured JSON logging — logs as machine-queryable events, not prose.

Defensive by design: _mask_sensitive is a net under the whole processor
chain, so even an accidental `token=` field leaves the process as
***MASKED***. It is a safety net, NOT permission to log secrets.
"""
import logging
import sys

import structlog
from structlog.typing import EventDict, WrappedLogger

SENSITIVE_KEYS = {"password", "token", "secret",
                  "national_id", "card_number"}


def _mask_sensitive(logger: WrappedLogger, method: str, event_dict: EventDict) -> EventDict:
    for key in list(event_dict):
        if key.lower() in SENSITIVE_KEYS:
            event_dict[key] = "***MASKED***"
    return event_dict


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(stream=sys.stdout, level=level)
    structlog.configure(processors=[
        structlog.contextvars.merge_contextvars,   # pulls trace_id into every line
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),  # UTC: incidents cross midnight
        _mask_sensitive,                           # MUST come before the renderer
        structlog.processors.JSONRenderer(),
    ])
