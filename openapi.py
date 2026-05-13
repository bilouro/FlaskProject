"""Auto-generated OpenAPI 3.1 spec.

Component schemas are derived from the Pydantic models in `books.schemas`
(`model_json_schema`), and paths come from a small per-endpoint registry
below. Beats the 200-line hand-rolled dict that lived in `app.py` and stays
in sync with the schemas automatically.
"""
from __future__ import annotations

from typing import Any

from books.schemas import BookCreate, BookOut, BookPatch, BookReplace


_REF = "#/components/schemas/{model}"


def _schema(model) -> dict[str, Any]:
    return model.model_json_schema(ref_template=_REF)


def _ref(name: str) -> dict[str, Any]:
    return {"$ref": f"#/components/schemas/{name}"}


def _json(schema_ref: dict[str, Any]) -> dict[str, Any]:
    return {"content": {"application/json": {"schema": schema_ref}}}


def _error_response(description: str) -> dict[str, Any]:
    return {"description": description, **_json(_ref("ErrorEnvelope"))}


ERROR_ENVELOPE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "error": {"type": "string"},
        "message": {"type": "string"},
        "code": {"type": "integer"},
        "path": {"type": "string"},
        "details": {"type": "array", "items": {"type": "object"}, "nullable": True},
    },
    "required": ["error", "message", "code", "path"],
}


def build_spec(title: str, version: str, prefix: str = "/v1") -> dict[str, Any]:
    book_id_param = {
        "name": "id",
        "in": "path",
        "required": True,
        "schema": {"type": "integer"},
    }

    paths: dict[str, Any] = {
        "/health": {
            "get": {
                "tags": ["meta"],
                "summary": "Liveness + DB readiness probe",
                "responses": {
                    "200": {
                        "description": "Health status",
                        **_json(
                            {
                                "type": "object",
                                "properties": {
                                    "status": {"type": "string"},
                                    "database": {"type": "string"},
                                },
                            }
                        ),
                    }
                },
            }
        },
        f"{prefix}/books/": {
            "get": {
                "tags": ["books"],
                "summary": "List all books",
                "responses": {
                    "200": {
                        "description": "List of books",
                        **_json({"type": "array", "items": _ref("BookOut")}),
                    }
                },
            },
            "post": {
                "tags": ["books"],
                "summary": "Create a new book",
                "requestBody": {"required": True, **_json(_ref("BookCreate"))},
                "responses": {
                    "201": {"description": "Created book", **_json(_ref("BookOut"))},
                    "409": _error_response("ISBN already exists"),
                    "415": _error_response("Wrong Content-Type"),
                    "422": _error_response("Validation error"),
                },
            },
        },
        f"{prefix}/books/{{id}}": {
            "get": {
                "tags": ["books"],
                "summary": "Get a book by ID",
                "parameters": [book_id_param],
                "responses": {
                    "200": {"description": "Book found", **_json(_ref("BookOut"))},
                    "404": _error_response("Book not found"),
                },
            },
            "put": {
                "tags": ["books"],
                "summary": "Replace a book",
                "parameters": [book_id_param],
                "requestBody": {"required": True, **_json(_ref("BookReplace"))},
                "responses": {
                    "200": {"description": "Updated book", **_json(_ref("BookOut"))},
                    "404": _error_response("Book not found"),
                    "409": _error_response("ISBN already exists"),
                    "422": _error_response("Validation error"),
                },
            },
            "patch": {
                "tags": ["books"],
                "summary": "Partially update a book",
                "parameters": [book_id_param],
                "requestBody": {"required": True, **_json(_ref("BookPatch"))},
                "responses": {
                    "200": {"description": "Updated book", **_json(_ref("BookOut"))},
                    "404": _error_response("Book not found"),
                    "409": _error_response("ISBN already exists"),
                    "422": _error_response("Validation error"),
                },
            },
            "delete": {
                "tags": ["books"],
                "summary": "Delete a book",
                "parameters": [book_id_param],
                "responses": {
                    "204": {"description": "Book deleted"},
                    "404": _error_response("Book not found"),
                },
            },
        },
    }

    return {
        "openapi": "3.1.0",
        "info": {
            "title": title,
            "version": version,
            "description": (
                "REST API for managing books. "
                "Built with Flask, SQLAlchemy, Pydantic, and Alembic."
            ),
        },
        "tags": [
            {"name": "meta", "description": "Service-level endpoints"},
            {"name": "books", "description": "Books domain"},
        ],
        "paths": paths,
        "components": {
            "schemas": {
                "BookCreate": _schema(BookCreate),
                "BookReplace": _schema(BookReplace),
                "BookPatch": _schema(BookPatch),
                "BookOut": _schema(BookOut),
                "ErrorEnvelope": ERROR_ENVELOPE_SCHEMA,
            }
        },
    }
