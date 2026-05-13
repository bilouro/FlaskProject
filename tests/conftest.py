"""Hermetic test fixtures.

The suite uses an **in-memory SQLite** database via SQLAlchemy. The
repository's lazy engine reads `SQLALCHEMY_DATABASE_URI` from the active
Flask config, so tests just point that at SQLite — no real Postgres needed.
"""
from __future__ import annotations

import pytest

from app import create_app
from books import repository
from books.models import Base
from config import TestConfig


class SqliteTestConfig(TestConfig):
    """In-memory SQLite. StaticPool (configured inside repository._build_engine)
    keeps the same connection alive across sessions so the schema persists."""

    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def app():
    flask_app = create_app(SqliteTestConfig)
    ctx = flask_app.app_context()
    ctx.push()
    # Build the engine now and create the schema.
    engine = repository.get_engine()
    Base.metadata.create_all(engine)
    try:
        yield flask_app
    finally:
        Base.metadata.drop_all(engine)
        repository.dispose_engine()
        ctx.pop()


@pytest.fixture()
def client(app):
    return app.test_client()


def _truncate(app):
    """Wipe the books table between tests."""
    engine = repository.get_engine()
    with engine.begin() as conn:
        conn.execute(Base.metadata.tables["books"].delete())


@pytest.fixture()
def seeded_db(app):
    """Empty the books table and insert two known rows. Returns their ids."""
    from sqlalchemy import insert

    _truncate(app)
    engine = repository.get_engine()
    books_table = Base.metadata.tables["books"]
    with engine.begin() as conn:
        result = conn.execute(
            insert(books_table).returning(books_table.c.id),
            [
                {"title": "Book 1", "author": "Author 1", "year": 2001, "isbn": "111"},
                {"title": "Book 2", "author": "Author 2", "year": 2002, "isbn": "222"},
            ],
        )
        return [row[0] for row in result.fetchall()]


@pytest.fixture()
def empty_db(app):
    _truncate(app)
    return None
