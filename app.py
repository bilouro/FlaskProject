from flask import Flask, jsonify

from config import DevConfig  # you can switch to ProdConfig in production
from db import get_connection
from books.routes import bp as books_bp


def create_app(config_class=DevConfig) -> Flask:
    """
    Application factory.

    Creates and configures the Flask app instance.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Register blueprints
    app.register_blueprint(books_bp, url_prefix="/books")

    # Health endpoint
    @app.get("/health")
    def health():
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    cur.fetchone()
            db_status = "ok"
        except Exception:
            db_status = "error"

        return jsonify({"status": "ok", "database": db_status})

    # Error handlers
    @app.errorhandler(400)
    @app.errorhandler(404)
    @app.errorhandler(415)
    def handle_error(err):
        return jsonify({"error": err.name, "message": err.description}), err.code

    @app.errorhandler(500)
    def handle_internal_error(err):
        return (
            jsonify(
                {
                    "error": "Internal Server Error",
                    "message": "An unexpected error occurred.",
                }
            ),
            500,
        )

    return app


# Global app instance for compatibility with tests and simple runs
app = create_app()


if __name__ == "__main__":
    # For development only. In production, use a proper WSGI server (e.g., gunicorn).
    app.run(host="0.0.0.0", port=5000, debug=app.config.get("DEBUG", False))