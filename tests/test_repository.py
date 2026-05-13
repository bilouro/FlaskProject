"""Unit-ish tests for books.repository — direct calls bypassing the HTTP layer.

These cover branches that aren't reachable through routes (e.g. update_book
called with an empty dict short-circuits before the DB session opens)."""
import pytest

from books import repository
from books.exceptions import DomainError, DuplicateISBNError
from books.models import Book


def test_domain_error_default_and_custom_message():
    assert DomainError().message == "Internal Server Error"
    assert DomainError("explicit").message == "explicit"


def test_update_book_with_empty_fields_returns_none(app):
    """`update_book` exits early when no fields are provided."""
    assert repository.update_book(1, {}) is None


def test_get_book_missing_returns_none(app, empty_db):
    assert repository.get_book(999) is None


def test_replace_book_missing_returns_none(app, empty_db):
    payload = {"title": "x", "author": "x", "year": 2000, "isbn": "no"}
    assert repository.replace_book(999, payload) is None


def test_update_book_missing_returns_none(app, empty_db):
    assert repository.update_book(999, {"year": 2020}) is None


def test_delete_book_missing_returns_false(app, empty_db):
    assert repository.delete_book(999) is False


def test_book_to_dict_includes_all_exposed_fields(app):
    book = Book(id=42, title="t", author="a", year=2024, isbn="i")
    book.status = "active"
    assert repository._book_to_dict(book) == {
        "id": 42,
        "title": "t",
        "author": "a",
        "year": 2024,
        "isbn": "i",
        "status": "active",
    }


def test_create_book_duplicate_isbn_raises(app, empty_db):
    repository.create_book({"title": "a", "author": "a", "year": 2020, "isbn": "DUP"})
    with pytest.raises(DuplicateISBNError):
        repository.create_book({"title": "b", "author": "b", "year": 2020, "isbn": "DUP"})


def test_replace_book_duplicate_isbn_raises(app, empty_db):
    a = repository.create_book({"title": "A", "author": "a", "year": 2020, "isbn": "AAA"})
    b = repository.create_book({"title": "B", "author": "b", "year": 2020, "isbn": "BBB"})
    with pytest.raises(DuplicateISBNError):
        repository.replace_book(
            a["id"], {"title": "A2", "author": "a", "year": 2020, "isbn": "BBB"}
        )
    # silence unused warning
    assert b["isbn"] == "BBB"


def test_update_book_duplicate_isbn_raises(app, empty_db):
    a = repository.create_book({"title": "A", "author": "a", "year": 2020, "isbn": "P-A"})
    repository.create_book({"title": "B", "author": "b", "year": 2020, "isbn": "P-B"})
    with pytest.raises(DuplicateISBNError):
        repository.update_book(a["id"], {"isbn": "P-B"})


def test_full_repository_round_trip(app, empty_db):
    created = repository.create_book(
        {"title": "rt", "author": "rt", "year": 2024, "isbn": "RT-1"}
    )
    book_id = created["id"]

    fetched = repository.get_book(book_id)
    assert fetched["isbn"] == "RT-1"

    listed = repository.list_books()
    assert any(b["id"] == book_id for b in listed)

    replaced = repository.replace_book(
        book_id, {"title": "rt2", "author": "rt", "year": 2025, "isbn": "RT-2"}
    )
    assert replaced["title"] == "rt2"
    assert replaced["isbn"] == "RT-2"

    patched = repository.update_book(book_id, {"year": 2030})
    assert patched["year"] == 2030

    assert repository.delete_book(book_id) is True
    assert repository.get_book(book_id) is None
