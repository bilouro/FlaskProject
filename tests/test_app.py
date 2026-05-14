"""App-level tests: factory, /health, /swagger.json, /docs, error handlers."""
from unittest.mock import patch

import pytest

from app import create_app
from books.exceptions import DomainError
from config import DevConfig, ProdConfig, TestConfig


# ---------------------------------------------------------------------------
# Application factory / configs
# ---------------------------------------------------------------------------

def test_create_app_defaults_to_dev_config():
    flask_app = create_app()
    assert flask_app.config["DEBUG"] is True
    assert flask_app.config["TESTING"] is False


@pytest.mark.parametrize(
    "cfg, debug, testing",
    [
        (DevConfig, True, False),
        (TestConfig, False, True),
        (ProdConfig, False, False),
    ],
)
def test_create_app_with_each_config(cfg, debug, testing):
    flask_app = create_app(cfg)
    assert flask_app.config["DEBUG"] is debug
    assert flask_app.config["TESTING"] is testing
    # DSN is correctly assembled from the base config
    assert flask_app.config["SQLALCHEMY_DATABASE_URI"].startswith("postgresql+psycopg2://")


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------

def test_health_ok(client):
    """With the SQLite test engine wired in, /health should respond ok."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "ok"
    assert data["database"] == "ok"
    assert "version" in data


def test_health_db_error(client):
    """If the engine raises, /health still returns 200 but database=error."""
    with patch("app.books_repository.get_engine", side_effect=RuntimeError("boom")):
        resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "ok"
    assert data["database"] == "error"


def test_root_returns_api_index(client):
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["name"] == "Books API"
    assert data["api"] == "/v1"
    assert "version" in data


# ---------------------------------------------------------------------------
# /swagger.json and /docs
# ---------------------------------------------------------------------------

def test_swagger_spec(client):
    resp = client.get("/swagger.json")
    assert resp.status_code == 200
    spec = resp.get_json()
    assert spec["openapi"].startswith("3.")
    assert spec["info"]["title"] == "Books API"
    # Sanity-check that all expected paths/methods are declared
    assert set(spec["paths"].keys()) == {"/health", "/v1/books/", "/v1/books/{id}"}
    assert set(spec["paths"]["/v1/books/{id}"].keys()) == {"get", "put", "patch", "delete"}
    # Component schemas are auto-derived from Pydantic models
    expected_schemas = {"BookCreate", "BookReplace", "BookPatch", "BookOut", "ErrorEnvelope"}
    assert expected_schemas <= set(spec["components"]["schemas"].keys())
    # BookOut surfaces the timestamps and status
    book_out_props = set(spec["components"]["schemas"]["BookOut"]["properties"].keys())
    assert {"id", "title", "author", "year", "isbn", "status", "created_at", "updated_at"} <= book_out_props


def test_docs_returns_swagger_ui(client):
    resp = client.get("/docs")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "swagger-ui" in body
    assert "/swagger.json" in body


# ---------------------------------------------------------------------------
# Error envelope handlers (400/404/405/415/500 + ValidationError + DomainError)
# ---------------------------------------------------------------------------

def test_404_handler_returns_standard_envelope(client):
    resp = client.get("/does-not-exist-anywhere")
    assert resp.status_code == 404
    data = resp.get_json()
    assert data["code"] == 404
    assert data["error"] == "Not Found"
    assert data["path"] == "/does-not-exist-anywhere"
    assert "message" in data


def test_405_handler_returns_standard_envelope(client, seeded_db):
    """An unsupported method on an existing route exercises the 405 branch."""
    resp = client.post(f"/v1/books/{seeded_db[0]}")
    assert resp.status_code == 405
    data = resp.get_json()
    assert data["code"] == 405
    assert data["path"] == f"/v1/books/{seeded_db[0]}"


def test_500_handler_returns_standard_envelope():
    """Register an ad-hoc route that raises an unhandled exception."""
    from tests.conftest import SqliteTestConfig

    flask_app = create_app(SqliteTestConfig)
    flask_app.config["PROPAGATE_EXCEPTIONS"] = False

    @flask_app.get("/__boom__")
    def boom():
        raise RuntimeError("unexpected")

    resp = flask_app.test_client().get("/__boom__")
    assert resp.status_code == 500
    data = resp.get_json()
    assert data["code"] == 500
    assert data["error"] == "Internal Server Error"
    assert data["message"] == "An unexpected error occurred."
    assert data["path"] == "/__boom__"


def test_415_handler_via_abort(client):
    resp = client.post("/v1/books/", data="not-json")
    assert resp.status_code == 415
    data = resp.get_json()
    assert data["code"] == 415
    assert data["error"] == "Unsupported Media Type"
    assert data["path"] == "/v1/books/"


def test_domain_error_handler_uses_envelope(client):
    """Direct exercise of the DomainError handler path."""
    err = DomainError("custom domain message")
    err.status_code = 418
    flask_app = create_app(__import__("tests.conftest", fromlist=["SqliteTestConfig"]).SqliteTestConfig)

    @flask_app.get("/__teapot__")
    def teapot():
        raise DomainError("I refuse")

    resp = flask_app.test_client().get("/__teapot__")
    data = resp.get_json()
    assert resp.status_code == 500  # default DomainError status
    assert data["message"] == "I refuse"
    assert data["path"] == "/__teapot__"


def test_validation_error_envelope_has_details(client, empty_db):
    """A bad payload surfaces structured `details` in the envelope."""
    resp = client.post(
        "/v1/books/",
        json={"title": "t", "author": "a", "year": "not-an-int", "isbn": "X"},
    )
    assert resp.status_code == 422
    data = resp.get_json()
    assert data["code"] == 422
    assert "year" in data["message"]
    assert isinstance(data["details"], list)
    assert any("year" in str(d.get("loc", "")) for d in data["details"])


# ---------------------------------------------------------------------------
# Benchmark helpers — /v1/sleep + X-Response-Time middleware
# ---------------------------------------------------------------------------

def test_x_response_time_header_present(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert "X-Response-Time" in resp.headers
    assert float(resp.headers["X-Response-Time"]) >= 0


def test_sleep_endpoint_default(client):
    resp = client.get("/v1/sleep")
    assert resp.status_code == 200
    assert resp.get_json() == {"slept_ms": 50}


def test_sleep_endpoint_with_ms_param(client):
    resp = client.get("/v1/sleep?ms=1")
    assert resp.status_code == 200
    assert resp.get_json() == {"slept_ms": 1}


def test_sleep_endpoint_invalid_ms_falls_back_to_default(client):
    resp = client.get("/v1/sleep?ms=not-a-number")
    assert resp.status_code == 200
    assert resp.get_json() == {"slept_ms": 50}


def test_sleep_endpoint_negative_ms_clamped_to_zero(client):
    resp = client.get("/v1/sleep?ms=-10")
    assert resp.status_code == 200
    assert resp.get_json() == {"slept_ms": 0}


def test_sleep_endpoint_uses_pg_sleep_on_postgres(monkeypatch):
    """Cover the postgresql dialect branch with a faked engine."""
    from unittest.mock import MagicMock

    from books import sleep as sleep_module

    fake_conn = MagicMock()
    fake_conn.__enter__ = MagicMock(return_value=fake_conn)
    fake_conn.__exit__ = MagicMock(return_value=False)
    fake_engine = MagicMock()
    fake_engine.dialect.name = "postgresql"
    fake_engine.connect.return_value = fake_conn

    monkeypatch.setattr(sleep_module.repository, "get_engine", lambda: fake_engine)

    from app import create_app
    from tests.conftest import SqliteTestConfig

    flask_app = create_app(SqliteTestConfig)
    resp = flask_app.test_client().get("/v1/sleep?ms=5")
    assert resp.status_code == 200
    assert resp.get_json() == {"slept_ms": 5}
    args, kwargs = fake_conn.execute.call_args
    assert "pg_sleep" in str(args[0])
    assert args[1] == {"s": 0.005}
