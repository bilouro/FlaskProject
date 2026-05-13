"""Flask application factory and WSGI entrypoint."""
from __future__ import annotations

import logging
from http import HTTPStatus

from flask import Flask, jsonify, request
from pydantic import ValidationError
from sqlalchemy import text

from books import repository as books_repository
from books.exceptions import DomainError
from books.routes import bp as books_bp
from config import DevConfig, get_settings
from logging_config import configure_logging
from openapi import build_spec


__version__ = "1.0.0"

log = logging.getLogger("app")


def create_app(config_class=DevConfig) -> Flask:
    """Application factory.

    Creates and configures the Flask app instance.
    """
    settings = get_settings()
    configure_logging("DEBUG" if config_class is DevConfig else "INFO")
    log.info(
        "starting app env=%s version=%s", getattr(settings, "env", "?"), __version__
    )

    app = Flask(__name__)
    app.config.from_object(config_class)

    # Register blueprints under the versioned prefix.
    app.register_blueprint(books_bp, url_prefix="/v1/books")

    # ------------------------------------------------------------------
    # Meta routes
    # ------------------------------------------------------------------

    @app.get("/")
    def root():
        return jsonify(
            {
                "name": "Books API",
                "version": __version__,
                "api": "/v1",
                "docs": "/docs",
                "openapi": "/swagger.json",
            }
        )

    @app.get("/health")
    def health():
        """Liveness + DB readiness probe."""
        try:
            engine = books_repository.get_engine()
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            db_status = "ok"
        except Exception:
            log.exception("health check: database query failed")
            db_status = "error"

        return jsonify(
            {"status": "ok", "database": db_status, "version": __version__}
        )

    @app.get("/swagger.json")
    def swagger_spec():
        return jsonify(build_spec(title="Books API", version=__version__))

    @app.get("/docs")
    def docs():
        return """
        <!DOCTYPE html>
        <html>
        <head>
          <title>Books API - Swagger UI</title>
          <link rel="stylesheet" type="text/css"
                href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css" />
        </head>
        <body>
          <div id="swagger-ui"></div>
          <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
          <script>
            window.onload = function() {
              SwaggerUIBundle({
                url: '/swagger.json',
                dom_id: '#swagger-ui'
              });
            };
          </script>
        </body>
        </html>
        """

    # ------------------------------------------------------------------
    # Error handlers — one consistent envelope:
    #   {"error", "message", "code", "path", "details" (optional)}
    # ------------------------------------------------------------------

    def _envelope(status_code, message, details=None):
        try:
            phrase = HTTPStatus(status_code).phrase
        except ValueError:
            phrase = "Error"
        body = {
            "error": phrase,
            "message": message,
            "code": status_code,
            "path": request.path,
        }
        if details is not None:
            body["details"] = details
        return jsonify(body), status_code

    @app.errorhandler(400)
    @app.errorhandler(404)
    @app.errorhandler(405)
    @app.errorhandler(415)
    def handle_http_error(err):
        return _envelope(err.code, err.description)

    @app.errorhandler(ValidationError)
    def handle_validation_error(err: ValidationError):
        errors = err.errors()
        primary = errors[0] if errors else {"msg": "validation error"}
        field = ".".join(str(p) for p in primary.get("loc", []))
        msg = primary.get("msg", "validation error")
        message = f"{field}: {msg}" if field else msg
        # Strip non-serialisable objects (Pydantic puts Exception instances
        # inside ctx for value_error types).
        clean = []
        for e in errors:
            entry = {k: v for k, v in e.items() if k != "ctx"}
            if "ctx" in e and isinstance(e["ctx"], dict):
                entry["ctx"] = {k: str(v) for k, v in e["ctx"].items()}
            clean.append(entry)
        return _envelope(422, message, details=clean)

    @app.errorhandler(DomainError)
    def handle_domain_error(err: DomainError):
        return _envelope(err.status_code, err.message)

    @app.errorhandler(500)
    def handle_internal_error(_err):
        return _envelope(500, "An unexpected error occurred.")

    return app


# Global app instance for compatibility with tests and simple runs
app = create_app()


if __name__ == "__main__":
    # For development only. In production, use a proper WSGI server (e.g., gunicorn).
    app.run(host="0.0.0.0", port=5001, debug=app.config.get("DEBUG", False))
