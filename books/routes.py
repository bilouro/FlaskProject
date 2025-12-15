from typing import Any, Dict

from flask import Blueprint, jsonify, request, abort

from . import repository


bp = Blueprint("books", __name__)

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


@bp.get("/")
def list_books():
    books = repository.list_books()
    return jsonify(books)


@bp.get("/<int:book_id>")
def get_book(book_id: int):
    book = repository.get_book(book_id)
    if not book:
        abort(404, description="Book not found")
    return jsonify(book)


@bp.post("/")
def create_book():
    data = _require_json_object()
    data = _validate_fields(data, required=True)

    book = repository.create_book(data)
    return jsonify(book), 201


@bp.put("/<int:book_id>")
def replace_book(book_id: int):
    data = _require_json_object()
    data = _validate_fields(data, required=True)

    book = repository.replace_book(book_id, data)
    if not book:
        abort(404, description="Book not found")
    return jsonify(book)


@bp.patch("/<int:book_id>")
def update_book(book_id: int):
    data = _require_json_object()
    data = _validate_fields(data, required=False)

    if not data:
        abort(400, description="No fields to update")

    book = repository.update_book(book_id, data)
    if not book:
        abort(404, description="Book not found")
    return jsonify(book)


@bp.delete("/<int:book_id>")
def delete_book(book_id: int):
    deleted = repository.delete_book(book_id)
    if not deleted:
        abort(404, description="Book not found")
    return "", 204