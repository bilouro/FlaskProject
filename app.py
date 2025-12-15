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
            "servers": [
                {"url": "http://127.0.0.1:5001"}
            ],
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

    # Error handlers
    @app.errorhandler(400)
    @app.errorhandler(404)
    @app.errorhandler(415)
    def handle_error(err):
        """
        Standard JSON error response:
        {
          "error": "Bad Request",
          "message": "...",
          "code": 400
        }
        """
        return (
            jsonify(
                {
                    "error": err.name,
                    "message": err.description,
                    "code": err.code,
                }
            ),
            err.code,
        )

    @app.errorhandler(500)
    def handle_internal_error(err):
        """
        Standardized 500 error response.
        """
        return (
            jsonify(
                {
                    "error": "Internal Server Error",
                    "message": "An unexpected error occurred.",
                    "code": 500,
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