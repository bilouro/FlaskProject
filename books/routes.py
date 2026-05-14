"""Books HTTP blueprint.

Validation is delegated to Pydantic v2 schemas (`books.schemas`). Both
`pydantic.ValidationError` and `books.exceptions.DomainError` are caught by
the app-level error handlers in `app.py`, so route bodies stay small and
free of try/except boilerplate.

Responses are serialised through `BookOut` so the wire format is owned by
a single Pydantic schema (and discoverable in the OpenAPI spec).
"""
from typing import Any, Dict, List

from flask import Blueprint, jsonify, request, abort

from books import repository
from books.exceptions import BookNotFoundError
from books.schemas import BookCreate, BookOut, BookPatch, BookReplace


bp = Blueprint("books", __name__)
# Accept both /v1/books and /v1/books/ — keeps client URLs flexible
# (notably k6 benchmark scripts hit the same path against both APIs).
bp.strict_slashes = False


def _require_json_object() -> Dict[str, Any]:
    if not request.is_json:
        abort(415, description="Content-Type must be application/json")
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        abort(400, description="Request body must be a JSON object")
    return data


def _serialise(book: Dict[str, Any]) -> Dict[str, Any]:
    return BookOut.model_validate(book).model_dump(mode="json")


def _serialise_list(books: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [_serialise(b) for b in books]


@bp.get("/")
def list_books():
    return jsonify(_serialise_list(repository.list_books()))


@bp.get("/<int:book_id>")
def get_book(book_id: int):
    book = repository.get_book(book_id)
    if not book:
        raise BookNotFoundError()
    return jsonify(_serialise(book))


@bp.post("/")
def create_book():
    payload = BookCreate.model_validate(_require_json_object())
    book = repository.create_book(payload.model_dump())
    return jsonify(_serialise(book)), 201


@bp.put("/<int:book_id>")
def replace_book(book_id: int):
    payload = BookReplace.model_validate(_require_json_object())
    book = repository.replace_book(book_id, payload.model_dump())
    if not book:
        raise BookNotFoundError()
    return jsonify(_serialise(book))


@bp.patch("/<int:book_id>")
def update_book(book_id: int):
    payload = BookPatch.model_validate(_require_json_object())
    fields = payload.model_dump(exclude_unset=True)
    book = repository.update_book(book_id, fields)
    if not book:
        raise BookNotFoundError()
    return jsonify(_serialise(book))


@bp.delete("/<int:book_id>")
def delete_book(book_id: int):
    if not repository.delete_book(book_id):
        raise BookNotFoundError()
    return "", 204
