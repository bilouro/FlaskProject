"""Benchmark helper endpoint.

`/v1/sleep?ms=N` issues `SELECT pg_sleep(N/1000.0)` against the configured
database, simulating a slow upstream I/O call. Sync handlers + threaded
gunicorn behave very differently from async runtimes under this workload;
the FastAPI sibling project exposes the same endpoint for direct
comparison.

Falls back to `SELECT 1` on dialects without pg_sleep (SQLite in tests).
"""
from flask import Blueprint, jsonify, request
from sqlalchemy import text

from books import repository


bp = Blueprint("sleep", __name__)


@bp.get("/sleep")
def sleep_endpoint():
    try:
        ms = int(request.args.get("ms", 50))
    except ValueError:
        ms = 50
    ms = max(0, ms)
    seconds = ms / 1000.0

    engine = repository.get_engine()
    with engine.connect() as conn:
        if engine.dialect.name == "postgresql":
            conn.execute(text("SELECT pg_sleep(:s)"), {"s": seconds})
        else:
            conn.execute(text("SELECT 1"))

    return jsonify({"slept_ms": ms})
