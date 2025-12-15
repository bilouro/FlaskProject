from flask import Flask, jsonify, request, abort
from typing import Dict, Any

app = Flask(__name__)

# Simple "Book" structure (no database): stored in memory
# {
#   "id": int,
#   "title": str,
#   "author": str,
#   "year": int,
#   "isbn": str
# }
BOOKS: Dict[int, Dict[str, Any]] = {
    1: {"id": 1, "title": "Clean Code", "author": "Robert C. Martin", "year": 2008, "isbn": "9780132350884"},
    2: {"id": 2, "title": "The Pragmatic Programmer", "author": "Andrew Hunt", "year": 1999, "isbn": "9780201616224"},
}
NEXT_ID = 3

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

    # Basic type checks (keep it simple)
    if "year" in data and not isinstance(data["year"], int):
        abort(400, description="Field 'year' must be an integer")
    for s in ("title", "author", "isbn"):
        if s in data and not isinstance(data[s], str):
            abort(400, description=f"Field '{s}' must be a string")

    return data


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/books")
def list_books():
    return jsonify(list(BOOKS.values()))


@app.get("/books/<int:book_id>")
def get_book(book_id: int):
    book = BOOKS.get(book_id)
    if not book:
        abort(404, description="Book not found")
    return jsonify(book)


@app.post("/books")
def create_book():
    global NEXT_ID
    data = _require_json_object()
    data = _validate_fields(data, required=True)

    book_id = NEXT_ID
    NEXT_ID += 1

    book = {"id": book_id, **data}
    BOOKS[book_id] = book

    return jsonify(book), 201


@app.put("/books/<int:book_id>")
def replace_book(book_id: int):
    if book_id not in BOOKS:
        abort(404, description="Book not found")

    data = _require_json_object()
    data = _validate_fields(data, required=True)

    BOOKS[book_id] = {"id": book_id, **data}
    return jsonify(BOOKS[book_id])


@app.patch("/books/<int:book_id>")
def update_book(book_id: int):
    book = BOOKS.get(book_id)
    if not book:
        abort(404, description="Book not found")

    data = _require_json_object()
    data = _validate_fields(data, required=False)

    book.update(data)
    return jsonify(book)


@app.delete("/books/<int:book_id>")
def delete_book(book_id: int):
    if book_id not in BOOKS:
        abort(404, description="Book not found")

    del BOOKS[book_id]
    return "", 204


@app.errorhandler(400)
@app.errorhandler(404)
@app.errorhandler(415)
def handle_error(err):
    # Return JSON errors (simple microservice-friendly style)
    return jsonify({"error": err.name, "message": err.description}), err.code


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)