"""Tests for the books blueprint covering every branch of routes.py."""
import json

import pytest
from sqlalchemy import select

from books import repository
from books.models import Book


def _count_books_with_isbn(isbn: str) -> int:
    with repository.get_sessionmaker()() as session:
        return session.scalar(
            select(Book.id).where(Book.isbn == isbn)
        ) is not None and 1 or 0


def _post(client, payload, content_type="application/json"):
    return client.post(
        "/v1/books/",
        data=json.dumps(payload) if content_type == "application/json" else payload,
        content_type=content_type,
    )


# ---------------------------------------------------------------------------
# GET /v1/books/
# ---------------------------------------------------------------------------

def test_list_books_returns_seeded_rows(client, seeded_db):
    resp = client.get("/v1/books/")
    assert resp.status_code == 200
    data = resp.get_json()
    assert [b["title"] for b in data] == ["Book 1", "Book 2"]
    expected_keys = {"id", "title", "author", "year", "isbn", "status"}
    assert expected_keys <= set(data[0].keys())


def test_list_books_empty(client, empty_db):
    resp = client.get("/v1/books/")
    assert resp.status_code == 200
    assert resp.get_json() == []


# ---------------------------------------------------------------------------
# GET /v1/books/<id>
# ---------------------------------------------------------------------------

def test_get_book_success(client, seeded_db):
    book_id = seeded_db[0]
    resp = client.get(f"/v1/books/{book_id}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["id"] == book_id
    assert data["title"] == "Book 1"


def test_get_book_not_found(client, empty_db):
    resp = client.get("/v1/books/999")
    assert resp.status_code == 404
    body = resp.get_json()
    assert body["message"] == "Book not found"
    assert body["path"] == "/v1/books/999"


# ---------------------------------------------------------------------------
# POST /v1/books/  — success + every validation branch
# ---------------------------------------------------------------------------

def test_create_book_success(client, empty_db):
    payload = {"title": "New", "author": "A", "year": 2023, "isbn": "ZZZ"}
    resp = _post(client, payload)
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["title"] == "New"
    assert data["status"] == "active"
    assert _count_books_with_isbn("ZZZ") == 1


def test_create_book_wrong_content_type_returns_415(client):
    resp = client.post("/v1/books/", data="not-json", content_type="text/plain")
    assert resp.status_code == 415
    assert "application/json" in resp.get_json()["message"]


def test_create_book_non_object_json_returns_400(client):
    resp = client.post(
        "/v1/books/",
        data=json.dumps(["not", "an", "object"]),
        content_type="application/json",
    )
    assert resp.status_code == 400
    assert "JSON object" in resp.get_json()["message"]


def test_create_book_unknown_field_returns_422(client):
    payload = {"title": "T", "author": "A", "year": 2020, "isbn": "X", "bogus": 1}
    resp = _post(client, payload)
    assert resp.status_code == 422
    body = resp.get_json()
    assert "bogus" in body["message"]
    assert any("bogus" in str(d.get("loc", "")) for d in body["details"])


def test_create_book_missing_required_returns_422(client):
    payload = {"title": "T", "author": "A", "year": 2020}  # no isbn
    resp = _post(client, payload)
    assert resp.status_code == 422
    body = resp.get_json()
    assert "isbn" in body["message"]


def test_create_book_year_must_be_integer(client):
    payload = {"title": "T", "author": "A", "year": "2020", "isbn": "X"}
    resp = _post(client, payload)
    assert resp.status_code == 422
    assert "year" in resp.get_json()["message"]


@pytest.mark.parametrize("field", ["title", "author", "isbn"])
def test_create_book_string_fields_must_be_strings(client, field):
    payload = {"title": "T", "author": "A", "year": 2020, "isbn": "X"}
    payload[field] = 123
    resp = _post(client, payload)
    assert resp.status_code == 422
    assert field in resp.get_json()["message"]


def test_create_book_duplicate_isbn_returns_409(client, empty_db):
    payload = {"title": "T", "author": "A", "year": 2020, "isbn": "DUP"}
    assert _post(client, payload).status_code == 201
    resp = _post(client, payload)
    assert resp.status_code == 409
    body = resp.get_json()
    assert body["error"] == "Conflict"
    assert "ISBN" in body["message"]


# ---------------------------------------------------------------------------
# PUT /v1/books/<id>
# ---------------------------------------------------------------------------

def test_replace_book_success(client, seeded_db):
    book_id = seeded_db[0]
    payload = {"title": "U", "author": "U", "year": 2010, "isbn": "U-1"}
    resp = client.put(f"/v1/books/{book_id}", json=payload)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["title"] == "U"
    assert data["isbn"] == "U-1"


def test_replace_book_not_found(client, empty_db):
    payload = {"title": "x", "author": "x", "year": 2000, "isbn": "no"}
    resp = client.put("/v1/books/999", json=payload)
    assert resp.status_code == 404


def test_replace_book_duplicate_isbn_returns_409(client, seeded_db):
    """PUT a book to the ISBN of another book."""
    other_id = seeded_db[1]
    payload = {"title": "x", "author": "x", "year": 2000, "isbn": "111"}  # collides with seeded_db[0]
    resp = client.put(f"/v1/books/{other_id}", json=payload)
    assert resp.status_code == 409


# ---------------------------------------------------------------------------
# PATCH /v1/books/<id>
# ---------------------------------------------------------------------------

def test_patch_book_success(client, seeded_db):
    book_id = seeded_db[0]
    resp = client.patch(f"/v1/books/{book_id}", json={"year": 2020})
    assert resp.status_code == 200
    assert resp.get_json()["year"] == 2020


def test_patch_book_empty_body_returns_422(client, seeded_db):
    book_id = seeded_db[0]
    resp = client.patch(f"/v1/books/{book_id}", json={})
    assert resp.status_code == 422
    assert "At least one field" in resp.get_json()["message"]


def test_patch_book_not_found(client, empty_db):
    resp = client.patch("/v1/books/999", json={"year": 2020})
    assert resp.status_code == 404


def test_patch_book_duplicate_isbn_returns_409(client, seeded_db):
    target = seeded_db[1]
    resp = client.patch(f"/v1/books/{target}", json={"isbn": "111"})
    assert resp.status_code == 409


# ---------------------------------------------------------------------------
# DELETE /v1/books/<id>
# ---------------------------------------------------------------------------

def test_delete_book_success(client, seeded_db):
    book_id = seeded_db[0]
    resp = client.delete(f"/v1/books/{book_id}")
    assert resp.status_code == 204
    assert resp.get_data() == b""

    with repository.get_sessionmaker()() as session:
        assert session.get(Book, book_id) is None


def test_delete_book_not_found(client, empty_db):
    resp = client.delete("/v1/books/999")
    assert resp.status_code == 404
