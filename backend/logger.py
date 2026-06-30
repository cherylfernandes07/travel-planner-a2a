# logger.py
# Structured JSON logging for the travel planner.
# Every log line is a JSON object with trace_id, agent,
# level, message, and timestamp — easy to filter in Railway.

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Optional


# ── JSON formatter ────────────────────────────────────────────

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level":     record.levelname,
            "message":   record.getMessage(),
            "logger":    record.name,
        }
        # attach any extra fields passed via extra={}
        for key in ("trace_id", "agent", "session_id", "user_id", "duration_ms"):
            if hasattr(record, key):
                log_entry[key] = getattr(record, key)

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


# ── Root logger setup ─────────────────────────────────────────

def setup_logging():
    """Call once at startup in main.py lifespan."""
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    # remove default handlers
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    root.addHandler(handler)

    # silence noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


# ── Per-module logger factory ─────────────────────────────────

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


# ── Trace context helper ──────────────────────────────────────
# Pass trace_id through as extra= on every log call:
#   logger.info("Agent started", extra={"trace_id": trace_id, "agent": "flight"})

class TraceLogger:
    """
    Wraps a logger with a fixed trace_id and agent name
    so you don't have to pass extra= on every call.
    """
    def __init__(self, logger: logging.Logger, trace_id: str, agent: Optional[str] = None):
        self._logger  = logger
        self._trace   = trace_id
        self._agent   = agent

    def _extra(self, kwargs: dict) -> dict:
        extra = {"trace_id": self._trace}
        if self._agent:
            extra["agent"] = self._agent
        kwargs.setdefault("extra", {}).update(extra)
        return kwargs

    def info(self, msg: str, **kwargs):
        self._logger.info(msg, **self._extra(kwargs))

    def warning(self, msg: str, **kwargs):
        self._logger.warning(msg, **self._extra(kwargs))

    def error(self, msg: str, **kwargs):
        self._logger.error(msg, **self._extra(kwargs))

    def debug(self, msg: str, **kwargs):
        self._logger.debug(msg, **self._extra(kwargs))