"""Targeted tests for branches not reachable from the normal HTTP/repo flows."""
import pytest
from flask import Flask

from books import repository
from config import Settings


def test_settings_database_url_short_circuits_dsn_build():
    """When APP_DATABASE_URL is set, it overrides the assembled DSN."""
    s = Settings(
        db_password="x",
        database_url="postgresql+psycopg2://override:pw@host:5432/db",
    )
    assert s.sqlalchemy_database_uri == (
        "postgresql+psycopg2://override:pw@host:5432/db"
    )


def test_resolve_database_uri_without_app_context_uses_baseconfig(monkeypatch):
    """_resolve_database_uri falls back to BaseConfig when no Flask context."""
    class _NoCtx:
        @property
        def config(self):
            raise RuntimeError("Working outside of application context.")

    monkeypatch.setattr(repository, "current_app", _NoCtx())
    uri = repository._resolve_database_uri()
    assert uri.startswith("postgresql+psycopg2://")


def test_build_engine_for_postgres_url():
    """Cover the non-sqlite branch of _build_engine without making a connection."""
    eng = repository._build_engine("postgresql+psycopg2://u:p@localhost:5432/db")
    assert eng.dialect.name == "postgresql"
    eng.dispose()


def test_dispose_engine_is_safe_when_engine_not_built(monkeypatch):
    """dispose_engine must short-circuit when nothing has been initialised."""
    monkeypatch.setattr(repository, "_engine", None)
    monkeypatch.setattr(repository, "_sessionmaker", None)
    # Should be a no-op, no exceptions.
    repository.dispose_engine()
    assert repository._engine is None


def test_envelope_falls_back_to_generic_phrase_for_unknown_status():
    """Trigger the `except ValueError` branch for an HTTP code unknown to
    the stdlib `HTTPStatus` enum (e.g. nginx-specific 499)."""
    from books.exceptions import DomainError
    from tests.conftest import SqliteTestConfig
    from app import create_app

    class _NginxError(DomainError):
        status_code = 499
        message = "Client Closed Request"

    flask_app = create_app(SqliteTestConfig)

    @flask_app.get("/__weird_code__")
    def weird():
        raise _NginxError()

    resp = flask_app.test_client().get("/__weird_code__")
    assert resp.status_code == 499
    body = resp.get_json()
    assert body["path"] == "/__weird_code__"
    assert body["error"] == "Error"  # fallback phrase
