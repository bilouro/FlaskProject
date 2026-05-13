from http import HTTPStatus

from flask import Flask, jsonify, request
from pydantic import ValidationError
from sqlalchemy import text

from books import repository as books_repository
from books.exceptions import DomainError
from books.routes import bp as books_bp
from config import DevConfig  # you can switch to ProdConfig in production


def create_app(config_class=DevConfig) -> Flask:
    """
    Application factory.

    Creates and configures the Flask app instance.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Register blueprints
    app.register_blueprint(books_bp, url_prefix="/books")

    # Health endpoint — pings the database through the SQLAlchemy engine
    # used by the repository, so it stays consistent with whatever DSN is
    # configured (Postgres in prod, SQLite in tests).
    @app.get("/health")
    def health():
        try:
            engine = books_repository.get_engine()
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            db_status = "ok"
        except Exception:
            db_status = "error"

        return jsonify({"status": "ok", "database": db_status})

    # Swagger/OpenAPI spec
    @app.get("/swagger.json")
    def swagger_spec():
        spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "Books API",
                "version": "1.0.0",
                "description": "Simple Books API example with Flask",
            },
            "paths": {
                "/health": {
                    "get": {
                        "summary": "Health check",
                        "responses": {
                            "200": {
                                "description": "Health status",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "status": {"type": "string"},
                                                "database": {"type": "string"},
                                            },
                                        }
                                    }
                                },
                            }
                        },
                    }
                },
                "/books/": {
                    "get": {
                        "summary": "List all books",
                        "responses": {
                            "200": {
                                "description": "List of books",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "array",
                                            "items": {
                                                "$ref": "#/components/schemas/Book"
                                            },
                                        }
                                    }
                                },
                            }
                        },
                    },
                    "post": {
                        "summary": "Create a new book",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/BookCreate"
                                    }
                                }
                            },
                        },
                        "responses": {
                            "201": {
                                "description": "Created book",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/Book"
                                        }
                                    }
                                },
                            },
                            "400": {"description": "Validation error"},
                        },
                    },
                },
                "/books/{id}": {
                    "get": {
                        "summary": "Get a book by ID",
                        "parameters": [
                            {
                                "name": "id",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "integer"},
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "Book found",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/Book"
                                        }
                                    }
                                },
                            },
                            "404": {"description": "Book not found"},
                        },
                    },
                    "put": {
                        "summary": "Replace a book",
                        "parameters": [
                            {
                                "name": "id",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "integer"},
                            }
                        ],
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/BookCreate"
                                    }
                                }
                            },
                        },
                        "responses": {
                            "200": {
                                "description": "Updated book",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/Book"
                                        }
                                    }
                                },
                            },
                            "404": {"description": "Book not found"},
                        },
                    },
                    "patch": {
                        "summary": "Partially update a book",
                        "parameters": [
                            {
                                "name": "id",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "integer"},
                            }
                        ],
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "title": {"type": "string"},
                                            "author": {"type": "string"},
                                            "year": {"type": "integer"},
                                            "isbn": {"type": "string"},
                                        },
                                    }
                                }
                            },
                        },
                        "responses": {
                            "200": {
                                "description": "Updated book",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/Book"
                                        }
                                    }
                                },
                            },
                            "404": {"description": "Book not found"},
                        },
                    },
                    "delete": {
                        "summary": "Delete a book",
                        "parameters": [
                            {
                                "name": "id",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "integer"},
                            }
                        ],
                        "responses": {
                            "204": {"description": "Book deleted"},
                            "404": {"description": "Book not found"},
                        },
                    },
                },
            },
            "components": {
                "schemas": {
                    "Book": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "title": {"type": "string"},
                            "author": {"type": "string"},
                            "year": {"type": "integer"},
                            "isbn": {"type": "string"},
                        },
                        "required": ["id", "title", "author", "year", "isbn"],
                    },
                    "BookCreate": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "author": {"type": "string"},
                            "year": {"type": "integer"},
                            "isbn": {"type": "string"},
                        },
                        "required": ["title", "author", "year", "isbn"],
                    },
                }
            },
        }
        return jsonify(spec)

    # Simple Swagger UI using CDN
    @app.get("/docs")
    def docs():
        html = """
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
        return html

    # -----------------------------------------------------------------
    # Error handlers — one consistent envelope for every 4xx/5xx response:
    #   {"error", "message", "code", "path", "details" (optional)}
    # -----------------------------------------------------------------

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
        return _envelope(400, message, details=clean)

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