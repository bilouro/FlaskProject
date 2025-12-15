import os
from typing import Dict, Any, List, Optional

import psycopg2
import psycopg2.extras
from flask import Flask, jsonify, request, abort

app = Flask(__name__)

# -----------------------------------------------------------------------------
# Database configuration
# -----------------------------------------------------------------------------
# In a real project, prefer environment variables instead of hardcoding.
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "dbname": os.getenv("DB_NAME", "app_db"),
    "user": os.getenv("DB_USER", "app_user"),
    "password": os.getenv("DB_PASSWORD", "bsd@0030"),
}


def get_connection():
    """
    Open a new PostgreSQL connection.

    Each handler uses a short-lived connection in a context manager.
    """
    return psycopg2.connect(**DB_CONFIG)


def row_to_book(row: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a DB row to the book JSON structure used by the API."""
    return {
        "id": row["id"],
        "title": row["title"],
        "author": row["author"],
        "year": row["year"],
        "isbn": row["isbn"],
    }


ALLOWED_FIELDS = {"title", "author", "year", "isbn"}


def _require_json_object() -> Dict[str, Any]:
    if not request.is_json:
        abort(415, description="Content-Type must be application/json")
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        abort(400, description="Request body must be a JSON object")
    return data


def _validate_fields(data: Dict[str, Any], required: bool) -> Dict[str, Any]:
    unknown = set(data.keys()) - ALLOWED_FIELDS
    if unknown:
        abort(400, description=f"Unknown field(s): {sorted(unknown)}")

    if required:
        missing = [f for f in sorted(ALLOWED_FIELDS) if f not in data]
        if missing:
            abort(400, description=f"Missing required field(s): {missing}")

    # Basic type checks
    if "year" in data and not isinstance(data["year"], int):
        abort(400, description="Field 'year' must be an integer")
    for s in ("title", "author", "isbn"):
        if s in data and not isinstance(data[s], str):
            abort(400, description=f"Field '{s}' must be a string")

    return data


# -----------------------------------------------------------------------------
# Health
# -----------------------------------------------------------------------------
@app.get("/health")
def health():
    # Optional: try a simple DB check
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        db_status = "ok"
    except Exception:
        db_status = "error"

    return jsonify({"status": "ok", "database": db_status})


# -----------------------------------------------------------------------------
# Books endpoints (PostgreSQL-backed)
# -----------------------------------------------------------------------------
@app.get("/books")
def list_books():
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, title, author, year, isbn
                FROM books
                ORDER BY id
                """
            )
            rows: List[Dict[str, Any]] = cur.fetchall()
    books = [row_to_book(row) for row in rows]
    return jsonify(books)


@app.get("/books/<int:book_id>")
def get_book(book_id: int):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, title, author, year, isbn
                FROM books
                WHERE id = %s
                """,
                (book_id,),
            )
            row: Optional[Dict[str, Any]] = cur.fetchone()

    if not row:
        abort(404, description="Book not found")

    return jsonify(row_to_book(row))


@app.post("/books")
def create_book():
    data = _require_json_object()
    data = _validate_fields(data, required=True)

    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO books (title, author, year, isbn)
                VALUES (%s, %s, %s, %s)
                RETURNING id, title, author, year, isbn
                """,
                (
                    data["title"],
                    data["author"],
                    data["year"],
                    data["isbn"],
                ),
            )
            row = cur.fetchone()
        conn.commit()

    return jsonify(row_to_book(row)), 201


@app.put("/books/<int:book_id>")
def replace_book(book_id: int):
    data = _require_json_object()
    data = _validate_fields(data, required=True)

    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                UPDATE books
                SET title = %s,
                    author = %s,
                    year = %s,
                    isbn = %s
                WHERE id = %s
                RETURNING id, title, author, year, isbn
                """,
                (
                    data["title"],
                    data["author"],
                    data["year"],
                    data["isbn"],
                    book_id,
                ),
            )
            row = cur.fetchone()
        conn.commit()

    if not row:
        abort(404, description="Book not found")

    return jsonify(row_to_book(row))


@app.patch("/books/<int:book_id>")
def update_book(book_id: int):
    data = _require_json_object()
    data = _validate_fields(data, required=False)

    if not data:
        abort(400, description="No fields to update")

    # Dynamically build SET clause
    fields = []
    values: List[Any] = []
    for key in sorted(data.keys()):
        fields.append(f"{key} = %s")
        values.append(data[key])

    values.append(book_id)

    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                f"""
                UPDATE books
                SET {", ".join(fields)}
                WHERE id = %s
                RETURNING id, title, author, year, isbn
                """,
                tuple(values),
            )
            row = cur.fetchone()
        conn.commit()

    if not row:
        abort(404, description="Book not found")

    return jsonify(row_to_book(row))


@app.delete("/books/<int:book_id>")
def delete_book(book_id: int):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM books
                WHERE id = %s
                RETURNING id
                """,
                (book_id,),
            )
            deleted = cur.fetchone()
        conn.commit()

    if not deleted:
        abort(404, description="Book not found")

    return "", 204


# -----------------------------------------------------------------------------
# Error handlers
# -----------------------------------------------------------------------------
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


# -----------------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    # For development only. In production, use a proper WSGI server.
    app.run(host="0.0.0.0", port=5000, debug=True)