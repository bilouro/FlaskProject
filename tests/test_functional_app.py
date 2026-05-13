"""Functional tests that hit a running Flask server via real HTTP.

These are opt-in: they require `python app.py` to be running on
http://127.0.0.1:5001. When the server is unreachable they are skipped, so
they never break the default `pytest` run."""
import json

import pytest
import requests


BASE_URL = "http://127.0.0.1:5001"


def _server_up() -> bool:
    """True only if /health responds 200 with the expected JSON shape — guards
    against unrelated services squatting on port 5000 (e.g. macOS AirPlay)."""
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=1)
        if resp.status_code != 200:
            return False
        data = resp.json()
        return isinstance(data, dict) and data.get("status") == "ok"
    except (requests.RequestException, ValueError):
        return False


pytestmark = [
    pytest.mark.functional,
    pytest.mark.skipif(not _server_up(), reason="Flask server is not running on :5000"),
]


def test_health_endpoint():
    resp = requests.get(f"{BASE_URL}/health", timeout=5)
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "ok"
    assert "database" in data


def test_full_book_crud_flow():
    # 1) initial list
    resp = requests.get(f"{BASE_URL}/books/", timeout=5)
    assert resp.status_code == 200
    initial_count = len(resp.json())

    # 2) create
    new_book = {
        "title": "Functional Test Book",
        "author": "Test Author",
        "year": 2024,
        "isbn": "FUNC-123456",
    }
    resp = requests.post(
        f"{BASE_URL}/books/",
        data=json.dumps(new_book),
        headers={"Content-Type": "application/json"},
        timeout=5,
    )
    assert resp.status_code == 201
    book_id = resp.json()["id"]

    try:
        # 3) get
        resp = requests.get(f"{BASE_URL}/books/{book_id}", timeout=5)
        assert resp.status_code == 200
        assert resp.json()["isbn"] == new_book["isbn"]

        # 4) put
        replaced = {
            "title": "Functional Test Book - Updated",
            "author": "Updated Author",
            "year": 2025,
            "isbn": "FUNC-654321",
        }
        resp = requests.put(
            f"{BASE_URL}/books/{book_id}",
            data=json.dumps(replaced),
            headers={"Content-Type": "application/json"},
            timeout=5,
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == replaced["title"]

        # 5) patch
        resp = requests.patch(
            f"{BASE_URL}/books/{book_id}",
            data=json.dumps({"year": 2030}),
            headers={"Content-Type": "application/json"},
            timeout=5,
        )
        assert resp.status_code == 200
        assert resp.json()["year"] == 2030
    finally:
        # 6) delete (best-effort cleanup)
        requests.delete(f"{BASE_URL}/books/{book_id}", timeout=5)

    # 7) ensure gone
    resp = requests.get(f"{BASE_URL}/books/{book_id}", timeout=5)
    assert resp.status_code == 404

    # 8) count restored
    resp = requests.get(f"{BASE_URL}/books/", timeout=5)
    assert resp.status_code == 200
    assert len(resp.json()) == initial_count
