import json
import logging
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from uuid import uuid4


class JsonFormatter(logging.Formatter):
    """Format application logs as structured JSON."""

    def format(self, record):
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "event": record.getMessage(),
        }

        for field in ("request_id", "operation", "duration_ms", "status"):
            if hasattr(record, field):
                payload[field] = getattr(record, field)

        return json.dumps(payload)


def configure_logging(level: str = "INFO") -> None:
    """Configure structured application logging."""
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())


def new_request_id() -> str:
    """Generate a unique correlation identifier."""
    return str(uuid4())


@contextmanager
def track_operation(operation: str, request_id: str = ""):
    """Measure execution time and log success or failure."""
    logger = logging.getLogger("research.telemetry")
    started = time.perf_counter()
    status = "success"

    try:
        yield
    except Exception:
        status = "failure"
        raise
    finally:
        duration_ms = round(
            (time.perf_counter() - started) * 1000, 2)

        logger.info(
            "operation_completed",
            extra={
                "request_id": request_id,
                "operation": operation,
                "duration_ms": duration_ms,
                "status": status,
            },
        )
