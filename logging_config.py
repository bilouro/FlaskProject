"""JSON-structured logging configuration.

Mirrors the FastAPI sibling project: every log line is emitted as one JSON
object on stdout, so a log shipper can parse fields without regex.
"""
from __future__ import annotations

import logging
import logging.config
from typing import Any


def build_logging_config(level: str) -> dict[str, Any]:
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": "pythonjsonlogger.json.JsonFormatter",
                "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
            }
        },
        "handlers": {
            "default": {
                "class": "logging.StreamHandler",
                "formatter": "json",
                "stream": "ext://sys.stdout",
            }
        },
        "loggers": {
            "werkzeug": {"handlers": ["default"], "level": level, "propagate": False},
            "sqlalchemy.engine": {"handlers": ["default"], "level": "WARNING", "propagate": False},
            "app": {"handlers": ["default"], "level": level, "propagate": False},
        },
        "root": {"handlers": ["default"], "level": level},
    }


def configure_logging(level: str) -> None:
    logging.config.dictConfig(build_logging_config(level))
