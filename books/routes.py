"""Books HTTP blueprint.

Validation is delegated to Pydantic v2 schemas (`books.schemas`). Both
`pydantic.ValidationError` and `books.exceptions.DomainError` are caught by
the app-level error handlers in `app.py`, so route bodies stay small and
free of try/except boilerplate.
"""
from typing import Any, Dict

from flask import Blueprint, jsonify, request, abort

from books import repository
from books.exceptions import BookNotFoundError
from books.schemas import BookCreate, BookPatch, BookReplace


bp = Blueprint("books", __name__)


def _require_json_object() -> Dict[str, Any]:
    if not request.is_json:
        abort(415, description="Content-Type must be application/json")
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        abort(400, description="Request body must be a JSON object")
    return data


@bp.get("/")
def list_books():
    return jsonify(repository.list_books())


@bp.get("/<int:book_id>")
def get_book(book_id: int):
    book = repository.get_book(book_id)
    if not book:
        raise BookNotFoundError()
    return jsonify(book)


@bp.post("/")
def create_book():
    payload = BookCreate.model_validate(_require_json_object())
    book = repository.create_book(payload.model_dump())
    return jsonify(book), 201


@bp.put("/<int:book_id>")
def replace_book(book_id: int):
    payload = BookReplace.model_validate(_require_json_object())
    book = repository.replace_book(book_id, payload.model_dump())
    if not book:
        raise BookNotFoundError()
    return jsonify(book)


@bp.patch("/<int:book_id>")
def update_book(book_id: int):
    payload = BookPatch.model_validate(_require_json_object())
    fields = payload.model_dump(exclude_unset=True)
    book = repository.update_book(book_id, fields)
    if not book:
        raise BookNotFoundError()
    return jsonify(book)


@bp.delete("/<int:book_id>")
def delete_book(book_id: int):
    if not repository.delete_book(book_id):
        raise BookNotFoundError()
    return "", 204
