"""Allowlisted JSON logs: never serialize exception messages, prompts or credentials."""
import json
import logging
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path


class SafeFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({"timestamp": datetime.now(timezone.utc).isoformat(),
                           "level": record.levelname, "event": record.getMessage(),
                           **getattr(record, "safe_fields", {})})


def configure_logging(data_dir: Path) -> None:
    directory = data_dir / "logs"
    directory.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("document_ai")
    if not logger.handlers:
        handler = RotatingFileHandler(directory / "events.log", maxBytes=2_000_000,
                                      backupCount=3, encoding="utf-8")
        handler.setFormatter(SafeFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False


def event(name: str, **safe_fields) -> None:
    logging.getLogger("document_ai").info(name, extra={"safe_fields": safe_fields})
